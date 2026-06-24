# 🛒 MicroShop — Microservices 

Chhota e-commerce: **3 microservices + Redis + Postgres** on AWS, self-managed Kubernetes, full Git→Production pipeline (Terraform · Ansible · Docker · K8s · GitHub Actions · Argo CD).

## Services
| Service | Kaam | Stateless? |
|---------|------|-----------|
| `frontend` | UI serve, API calls | ✅ |
| `catalog-api` | products CRUD + Redis cache | ✅ |
| `order-api` | orders, calls catalog-api (inter-service) | ✅ |

## Data
- **Postgres** (RDS) — products + orders (durable, stateful)
- **Redis** — product cache (fast)

## Architecture
```
User → frontend → catalog-api ↔ order-api
                    │              │
                  Redis        Postgres (RDS)
       (order-api → catalog-api = inter-service via K8s service DNS)
```

## Pipeline (8 phases)
P1 Git · P2 Docker+ECR · P3 Terraform · P4 Ansible(kubeadm) · P5 Deploy · P6 CI(Actions) · P7 GitOps(Argo) · P8 Polish(ingress/monitoring/HPA/TLS)

## ⚠️ Cost
AWS ap-south-1. **Daily `terraform destroy`** after each session. Billing alert ($20) set.
