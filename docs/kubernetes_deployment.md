# Kubernetes deployment

We advise you to have a separate `deployment` for scale `up/down` your `kafka consumers` independently of your `application`.
This is useful because you might need more/less `kafka consumers` (replicas) to handle events and the number of replicas
most of the time is different from the `application replicas`.

```yaml
# Source: django-streaming-example/templates/streaming-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-streaming-example-worker
  labels:
    app.kubernetes.io/name: django-streaming-example
    app.kubernetes.io/instance: django-streaming-example-preview-latest
    app.kubernetes.io/version: latest
    app.kubernetes.io/component: backend
    app.kubernetes.io/managed-by: Helm
    app: django-streaming-example
spec:
  replicas: 1
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 10%
  selector:
    matchLabels:
      app: django-streaming-example
  template:
    metadata:
      labels:
        app: django-streaming-example
      annotations:
        co.elastic.logs/enabled: "true"
    spec:
      serviceAccountName: django-streaming-example-service-account
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 1
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - django-streaming-example
              topologyKey: kubernetes.io/hostname
          - weight: 1
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - django-streaming-example
              topologyKey: failure-domain.beta.kubernetes.io/zone
      containers:
      - name: streaming
        image: django-streams:latest
        imagePullPolicy: IfNotPresent
        securityContext:
          runAsUser: 1000
        args: ["make", "worker"]
        resources:
          limits:
            cpu: 600m
            memory: 256Mi
          requests:
            cpu: 300m
            memory: 128Mi
        envFrom:
          - configMapRef:
              name: django-streaming-example-config
        volumeMounts:
        - mountPath: /secrets
          name: secrets-folder
      volumes:
      - name: secrets-folder
        emptyDir:
          medium: Memory
          sizeLimit: 1Mi
```
