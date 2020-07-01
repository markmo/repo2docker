#!/usr/bin/env bash

USER_NAME=$REPO_NAME
kubectl -n kiosk create serviceaccount $USER_NAME

# create account
cat <<EOF | kubectl apply -f -
apiVersion: tenancy.kiosk.sh/v1alpha1
kind: Account
metadata:
  name: $USER_NAME
spec:
  subjects:
  - kind: User
    name: $USER_NAME
    apiGroup: rbac.authorization.k8s.io
EOF

cat <<EOF | kubectl apply -f -
apiVersion: tenancy.kiosk.sh/v1alpha1
kind: Account
metadata:
  name: $USER_NAME
spec:
  subjects:
  - kind: ServiceAccount
    name: $USER_NAME
    namespace: kiosk
EOF

# create space
cat <<EOF | kubectl apply -f -
apiVersion: tenancy.kiosk.sh/v1alpha1
kind: Space
metadata:
  name: ${USER_NAME}-space
spec:
  account: $USER_NAME
EOF

# set account quota limits
cat <<EOF | kubectl apply -f -
apiVersion: config.kiosk.sh/v1alpha1
kind: AccountQuota
metadata:
  name: default-user-limits
spec:
  account: $USER_NAME
  quota:
    hard:
      pods: "5"
      limits.cpu: "2"
      limits.memory: 2Gi
EOF

KUBECONFIG_PATH="$HOME/.kube/config-kiosk"

kubectl config view --minify --raw >$KUBECONFIG_PATH
export KUBECONFIG=$KUBECONFIG_PATH

CURRENT_CONTEXT=$(kubectl config current-context)
kubectl config rename-context $CURRENT_CONTEXT kiosk-admin

CLUSTER_NAME=$(kubectl config view -o jsonpath="{.clusters[].name}")
ADMIN_USER=$(kubectl config view -o jsonpath="{.users[].name}")

SA_NAME=$(kubectl -n kiosk get serviceaccount $USER_NAME -o jsonpath="{.secrets[0].name}")
SA_TOKEN=$(kubectl -n kiosk get secret $SA_NAME -o jsonpath="{.data.token}" | base64 -d)

kubectl config set-credentials $USER_NAME --token=$SA_TOKEN
kubectl config set-context kiosk-user --cluster=$CLUSTER_NAME --user=$USER_NAME
kubectl config use-context kiosk-user

# Optional: delete admin context and user
kubectl config unset contexts.kiosk-admin
kubectl config unset users.$ADMIN_USER

export KUBECONFIG=$KUBECONFIG_PATH
