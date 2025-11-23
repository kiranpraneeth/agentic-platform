# Deployment and Infrastructure Guide

## Overview
Progressive deployment strategy starting with simple Docker Compose for local development, scaling to Kubernetes for production multi-tenant, multi-region deployment.

## Deployment Phases

### Phase 1: Local Development (Docker Compose)
### Phase 2: Single-Region Production (Kubernetes)
### Phase 3: Multi-Tenant Production (K8s + Namespaces)
### Phase 4: Multi-Region Production (Global K8s)

---

## Phase 1: Local Development Setup

### Requirements
- Docker and Docker Compose
- 8GB RAM minimum
- 20GB disk space

### Docker Compose Architecture

**Services to include:**
- API server (FastAPI/Node.js)
- PostgreSQL database
- Redis (cache + queue)
- Vector database (pgvector or Pinecone)
- (Optional) RabbitMQ for message queue
- (Optional) Temporal for workflows

### docker-compose.yml Structure

Services needed:
```
- api: Main API server
- postgres: PostgreSQL with pgvector extension
- redis: Redis for caching and task queue
- worker: Background job processor
- nginx: Reverse proxy (optional for local)
```

### Environment Variables

Required environment variables:
```
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/dbname
REDIS_URL=redis://redis:6379

# LLM Providers
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...

# Vector Store
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...

# Application
SECRET_KEY=random_secret_key
JWT_SECRET=jwt_secret_key
API_VERSION=v1
LOG_LEVEL=info

# MCP
MCP_SERVER_PATH=/app/mcp-servers
```

### Setup Commands

```bash
# Clone repository
git clone <repo-url>
cd agentic-platform

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Create initial admin user
docker-compose exec api python scripts/create_admin.py

# Check logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Database Initialization

Steps needed:
1. Run initial migration to create tables
2. Seed data for development (sample tenants, agents)
3. Create database indexes
4. Enable pgvector extension if using

### Health Checks

Implement health check endpoints:
- `/health`: Basic health check
- `/health/live`: Liveness probe
- `/health/ready`: Readiness probe (checks DB, Redis connectivity)

### Development Workflow

1. Code changes hot-reload automatically
2. Database migrations: `docker-compose exec api alembic revision -m "description"`
3. Run tests: `docker-compose exec api pytest`
4. Access API: http://localhost:8000
5. Access docs: http://localhost:8000/docs

---

## Phase 2: Single-Region Production (Kubernetes)

### Infrastructure Requirements

**Kubernetes Cluster:**
- Managed Kubernetes (EKS, GKE, AKS)
- 3+ nodes for redundancy
- Auto-scaling enabled
- Node size: 4 CPU, 16GB RAM minimum

**External Services:**
- Managed PostgreSQL (RDS, Cloud SQL, Azure Database)
- Managed Redis (ElastiCache, Memorystore, Azure Cache)
- Object storage (S3, GCS, Azure Blob)
- Load balancer (ALB, Cloud Load Balancing)

### Kubernetes Resources

**Deployments needed:**
- API server deployment (3+ replicas)
- Worker deployment (2+ replicas)
- Background job processor

**Services:**
- API service (LoadBalancer type)
- Internal services (ClusterIP)

**ConfigMaps:**
- Application configuration
- MCP server configurations
- Logging configuration

**Secrets:**
- Database credentials
- API keys (LLM providers)
- JWT secrets
- Encryption keys

**Ingress:**
- TLS termination
- Path-based routing
- Rate limiting rules

**Persistent Volumes:**
- Shared storage for document uploads
- Log storage (if not using external logging)

### Kubernetes Manifests Structure

```
k8s/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
├── overlays/
│   ├── development/
│   ├── staging/
│   └── production/
└── helm/
    └── agentic-platform/
        ├── Chart.yaml
        ├── values.yaml
        └── templates/
```

### Deployment Strategy

**Rolling Updates:**
- MaxUnavailable: 25%
- MaxSurge: 25%
- Progressive rollout
- Automated rollback on failure

**Readiness/Liveness Probes:**
```
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Auto-Scaling Configuration

**Horizontal Pod Autoscaler (HPA):**
- Min replicas: 3
- Max replicas: 20
- Target CPU: 70%
- Target memory: 80%
- Custom metrics: request rate, queue depth

**Vertical Pod Autoscaler (VPA):**
- Auto-adjust resource requests/limits
- Based on historical usage

**Cluster Autoscaler:**
- Add nodes when pods pending
- Remove nodes when underutilized

### Database Setup

**Managed PostgreSQL:**
- Multi-AZ for high availability
- Automated backups (daily)
- Point-in-time recovery enabled
- Read replicas for read-heavy workloads
- Connection pooling (PgBouncer)

**Schema Management:**
- Automated migrations on deployment
- Blue-green deployment for major changes
- Rollback capability

### Redis Setup

**Configuration:**
- Cluster mode for scalability
- Persistence enabled (AOF + RDS)
- Separate instances for cache vs queue
- Connection pooling

### Secrets Management

**Options:**
- Kubernetes Secrets (basic)
- HashiCorp Vault (recommended)
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault

**Best Practices:**
- Encrypt secrets at rest
- Rotate secrets regularly
- Use external secrets operator
- Never commit secrets to Git

### CI/CD Pipeline

**Build Stage:**
1. Run linters and code quality checks
2. Run unit tests
3. Build Docker image
4. Tag with git commit SHA
5. Push to container registry
6. Scan image for vulnerabilities

**Deploy Stage:**
1. Update Kubernetes manifests
2. Apply database migrations
3. Deploy to staging
4. Run integration tests
5. Manual approval for production
6. Deploy to production
7. Run smoke tests
8. Monitor for errors

**Tools:**
- GitHub Actions / GitLab CI / Jenkins
- ArgoCD for GitOps
- Helm for package management
- Kustomize for overlays

### Monitoring and Logging

**Metrics (Prometheus + Grafana):**
- API request rate, latency, errors
- Database connection pool usage
- Redis memory usage
- Agent execution metrics
- Token usage per tenant
- Queue depth and processing time

**Logging (ELK Stack or Loki):**
- Structured JSON logs
- Centralized log aggregation
- Log retention: 30 days hot, 90 days cold
- Search and alerting

**Distributed Tracing (Jaeger):**
- Trace requests across services
- Identify bottlenecks
- Debug multi-agent workflows

**Alerting:**
- High error rates
- Increased latency
- Database connection issues
- Quota exceeded
- Service down

### Backup and Disaster Recovery

**Database Backups:**
- Automated daily backups
- Retain for 30 days
- Test restore monthly
- Cross-region backup replication

**Application Backups:**
- Git repository (infrastructure as code)
- Docker images in registry
- Configuration in version control

**Disaster Recovery Plan:**
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes
- Documented runbooks
- Regular DR drills

---

## Phase 3: Multi-Tenant Production

### Tenant Isolation Strategies

**Option 1: Shared Database with Row-Level Security**
- Single database, tenant_id on all tables
- PostgreSQL RLS policies
- Application-level checks
- Most cost-effective

**Option 2: Schema-Per-Tenant**
- Separate schema for each tenant
- Better isolation
- Manageable for hundreds of tenants

**Option 3: Database-Per-Tenant**
- Separate database instance per tenant
- Complete isolation
- Best for enterprise customers
- Higher cost and complexity

**Recommended**: Hybrid approach
- Shared for small/medium tenants
- Dedicated for enterprise

### Namespace Strategy

Use Kubernetes namespaces for logical separation:
```
- namespace: tenant-{tenant_id} (for dedicated resources)
- namespace: shared-services (for multi-tenant components)
- namespace: platform-core (for platform services)
```

### Resource Quotas per Tenant

Implement ResourceQuota in Kubernetes:
```
CPU limits per tenant
Memory limits per tenant
Pod count limits
Storage limits
```

Implement application-level quotas:
- API calls per day
- Token usage per month
- Agent execution time
- Storage space

### Tenant Provisioning

Automated tenant onboarding:
1. Create tenant record in database
2. Generate API keys
3. Create namespace (if dedicated)
4. Apply resource quotas
5. Set up monitoring
6. Send welcome email

### Cost Allocation

Track costs per tenant:
- Compute resources used
- Storage consumed
- API calls made
- LLM tokens used
- Database queries

Generate monthly cost reports per tenant

---

## Phase 4: Multi-Region Production

### Architecture

**Regions:**
- Primary: US-East
- Secondary: EU-West, Asia-Pacific
- Each region: Full K8s cluster

**Traffic Routing:**
- Global load balancer (Cloudflare, AWS Global Accelerator)
- GeoDNS for region routing
- Failover to nearest region

### Data Replication

**Database:**
- Multi-region PostgreSQL (Aurora Global, CockroachDB)
- Active-active or active-passive replication
- Replication lag monitoring
- Conflict resolution strategy

**Options:**
- **Aurora Global Database**: 1-second replication, read replicas in each region
- **CockroachDB**: Geo-distributed, strong consistency
- **PostgreSQL with Logical Replication**: More control, requires management

**Cache:**
- Regional Redis clusters
- Cache invalidation across regions
- Eventual consistency acceptable for cache

**Object Storage:**
- S3 cross-region replication
- Or use multi-region buckets
- CDN for global content delivery

### Service Mesh

Implement Istio or Linkerd for:
- Service-to-service communication
- Traffic management (routing, retries)
- Security (mTLS between services)
- Observability (metrics, traces)
- Circuit breaking and fault injection

### Cross-Region Communication

**Synchronous:**
- Direct API calls between regions (for critical operations)
- Latency considerations
- Timeout and retry policies

**Asynchronous:**
- Message queue with cross-region replication (Kafka)
- Event-driven architecture
- Eventual consistency

### Data Residency and Compliance

**Requirements:**
- GDPR: EU data must stay in EU
- Data sovereignty: Some countries require local storage
- Data classification: Identify sensitive data

**Implementation:**
- Region-specific data storage
- Compliance metadata on tenants
- Routing based on data residency rules
- Encryption at rest and in transit

**Tenant Configuration:**
```json
{
  "tenant_id": "uuid",
  "primary_region": "eu-west",
  "data_residency": "eu",
  "allowed_regions": ["eu-west", "eu-central"],
  "compliance_requirements": ["gdpr", "iso27001"]
}
```

### Regional Failover

**Health Checks:**
- Monitor region health
- Database connectivity
- Service availability
- Latency thresholds

**Failover Strategy:**
1. Detect region failure
2. Update global load balancer
3. Route traffic to healthy region
4. Promote read replica to primary (if needed)
5. Alert operations team
6. Post-mortem after recovery

**Failover Time Target:**
- Detection: < 30 seconds
- Failover: < 2 minutes
- Full recovery: < 15 minutes

### Global Monitoring

**Centralized Monitoring:**
- Aggregate metrics from all regions
- Global dashboard (Grafana)
- Cross-region latency tracking
- Region health status

**Alerting:**
- Region-specific alerts
- Global alerts for critical issues
- On-call rotation by region
- Escalation policies

### Cost Optimization

**Strategies:**
- Use spot instances for non-critical workloads
- Right-size pods based on actual usage
- Auto-scaling to match demand
- Reserved instances for baseline capacity
- Archive old data to cold storage
- CDN for static assets
- Optimize database queries
- Connection pooling
- Cache frequently accessed data

**Cost Monitoring:**
- Track costs per region
- Cost per tenant
- Cost per service
- Identify optimization opportunities
- Set budget alerts

---

## Infrastructure as Code

### Terraform Structure

```
terraform/
├── modules/
│   ├── kubernetes-cluster/
│   ├── database/
│   ├── redis/
│   ├── networking/
│   └── monitoring/
├── environments/
│   ├── development/
│   ├── staging/
│   └── production/
└── global/
    └── dns/
```

**Required Terraform Modules:**
- VPC and networking
- Kubernetes cluster (EKS/GKE/AKS)
- RDS/managed database
- Redis/ElastiCache
- S3 buckets
- IAM roles and policies
- Load balancers
- DNS records
- Monitoring stack

### Helm Charts

**Chart Structure:**
```
helm/agentic-platform/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── configmap.yaml
    ├── secrets.yaml
    ├── hpa.yaml
    └── servicemonitor.yaml
```

**Values Configuration:**
- Environment-specific values
- Resource requests/limits
- Replica counts
- Image tags
- Feature flags

### GitOps with ArgoCD

**Setup:**
1. Install ArgoCD in cluster
2. Connect to Git repository
3. Define applications
4. Configure sync policies
5. Set up notifications

**Application Definitions:**
- One app per environment
- Automatic sync on Git push
- Self-healing enabled
- Prune resources on delete

**Benefits:**
- Declarative infrastructure
- Version control for deployments
- Easy rollbacks
- Audit trail
- Disaster recovery

---

## Security Best Practices

### Network Security

**Kubernetes Network Policies:**
- Restrict pod-to-pod communication
- Allow only necessary traffic
- Deny by default

**Firewall Rules:**
- Whitelist IP ranges
- Restrict database access to application layer
- No public internet access for internal services

**VPC Configuration:**
- Private subnets for workloads
- Public subnets for load balancers
- NAT gateways for outbound traffic
- VPC peering for cross-region

### Application Security

**Authentication:**
- API key rotation
- JWT with short expiration
- OAuth 2.0 for third-party
- MFA for admin access

**Authorization:**
- RBAC for Kubernetes
- Role-based access in application
- Principle of least privilege
- Regular permission audits

**Data Encryption:**
- TLS 1.3 for all external traffic
- Encrypt data at rest
- Encrypt database connections
- Encrypt sensitive environment variables

**Input Validation:**
- Validate all API inputs
- Sanitize user data
- SQL injection prevention
- XSS protection

**Dependency Management:**
- Regular dependency updates
- Security scanning (Snyk, Dependabot)
- Vulnerability patching
- License compliance

### Compliance

**SOC 2:**
- Access controls
- Audit logging
- Incident response plan
- Data encryption
- Regular security assessments

**GDPR:**
- Data processing agreements
- Right to erasure
- Data portability
- Privacy by design
- Data breach notification

**HIPAA (if applicable):**
- BAA agreements
- Encryption requirements
- Access controls
- Audit logging
- PHI protection

---

## Performance Optimization

### API Performance

**Caching Strategy:**
- Cache GET responses
- Cache-Control headers
- ETags for conditional requests
- Redis for session data
- CDN for static assets

**Database Optimization:**
- Query optimization
- Proper indexing
- Connection pooling
- Read replicas for read-heavy loads
- Database query caching

**Async Processing:**
- Background jobs for heavy tasks
- Message queues for decoupling
- Webhook delivery async
- Document processing async

### LLM Performance

**Request Optimization:**
- Batch requests when possible
- Stream responses for better UX
- Timeout management
- Retry with exponential backoff
- Circuit breaker pattern

**Cost Optimization:**
- Cache common responses
- Use smaller models when appropriate
- Prompt optimization
- Token counting and limits
- Request deduplication

### Vector Database Performance

**Optimization:**
- Appropriate index type (HNSW, IVF)
- Shard by tenant
- Query result caching
- Batch embedding generation
- Index optimization

---

## Migration Strategies

### Zero-Downtime Deployment

**Blue-Green Deployment:**
1. Deploy new version (green)
2. Test green environment
3. Switch traffic to green
4. Keep blue for quick rollback
5. Decommission blue after validation

**Canary Deployment:**
1. Deploy new version to small subset
2. Monitor metrics and errors
3. Gradually increase traffic
4. Rollback if issues detected
5. Full rollout when validated

**Rolling Deployment:**
1. Update pods one by one
2. Health checks before next pod
3. Automatic rollback on failure
4. Progressive rollout

### Database Migration

**Best Practices:**
- Backward compatible changes
- Additive changes first (add columns)
- Run old and new code simultaneously
- Remove deprecated columns later
- Test migrations on staging
- Backup before migration
- Have rollback plan

**Large Migrations:**
- Background migration for large tables
- Batch processing
- Progress tracking
- Pause/resume capability
- Minimal locking

### Data Migration

**Multi-Tenant to Multi-Region:**
1. Identify tenant's target region
2. Snapshot tenant data
3. Restore to target region database
4. Replicate recent changes
5. Switch tenant routing
6. Verify data integrity
7. Archive old data

---

## Runbooks and Procedures

### Incident Response

**Process:**
1. Alert triggered
2. On-call engineer notified
3. Assess severity
4. Create incident channel
5. Investigate and mitigate
6. Communicate status
7. Resolve incident
8. Post-mortem

**Severity Levels:**
- P0: Critical (service down)
- P1: Major (degraded performance)
- P2: Minor (non-critical feature)
- P3: Low (cosmetic issue)

### Common Operations

**Scaling Up:**
```bash
# Scale API deployment
kubectl scale deployment api --replicas=10

# Update HPA limits
kubectl patch hpa api --patch '{"spec":{"maxReplicas":20}}'
```

**Database Maintenance:**
```bash
# Run vacuum
kubectl exec -it postgres-0 -- psql -c "VACUUM ANALYZE;"

# Check slow queries
kubectl exec -it postgres-0 -- psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

**Cache Clearing:**
```bash
# Clear Redis cache
kubectl exec -it redis-0 -- redis-cli FLUSHDB
```

**View Logs:**
```bash
# API logs
kubectl logs -f deployment/api --tail=100

# All pods in namespace
kubectl logs -f -l app=api --all-containers=true
```

**Restart Service:**
```bash
# Rolling restart
kubectl rollout restart deployment/api

# Check rollout status
kubectl rollout status deployment/api
```

### Maintenance Windows

**Planning:**
- Schedule during low traffic
- Communicate to customers
- Backup before changes
- Test in staging first
- Have rollback plan
- Monitor during and after

**Communication:**
- Status page updates
- Email notifications
- In-app messaging
- API response headers

---

## Testing in Production

### Smoke Tests

Run after deployment:
- Health check endpoints
- Create agent
- Execute simple task
- Query knowledge base
- List resources

### Load Testing

**Tools:** k6, Locust, JMeter

**Scenarios:**
- Normal load (baseline)
- Peak load (2x normal)
- Stress test (find breaking point)
- Spike test (sudden traffic increase)
- Soak test (sustained load)

**Metrics to Monitor:**
- Response times (p50, p95, p99)
- Error rates
- Throughput (requests/sec)
- Resource utilization
- Database connections

### Chaos Engineering

**Tools:** Chaos Mesh, Litmus

**Experiments:**
- Pod failures
- Network latency injection
- CPU stress
- Memory pressure
- Database unavailability
- Region failure

**Goal:** Verify resilience and failover

---

## Documentation Requirements

### For Developers

- Local development setup guide
- API documentation (OpenAPI)
- Architecture diagrams
- Database schema documentation
- Coding standards and guidelines
- Testing guide
- Deployment process

### For Operations

- Infrastructure documentation
- Runbooks for common operations
- Incident response procedures
- Monitoring and alerting guide
- Backup and recovery procedures
- Security policies
- On-call rotation schedule

### For End Users

- Getting started guide
- API reference and examples
- SDK documentation
- Best practices
- Troubleshooting guide
- FAQ
- Changelog

---

## Deployment Checklist

### Pre-Deployment

- [ ] Code reviewed and approved
- [ ] Tests passing (unit, integration)
- [ ] Security scan passed
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Stakeholders notified
- [ ] Staging deployment successful
- [ ] Monitoring and alerts configured

### During Deployment

- [ ] Backup database
- [ ] Enable maintenance mode (if needed)
- [ ] Run database migrations
- [ ] Deploy application
- [ ] Smoke tests passed
- [ ] Monitor error rates
- [ ] Check resource usage
- [ ] Verify critical flows

### Post-Deployment

- [ ] Smoke tests completed
- [ ] Monitor for 30 minutes
- [ ] Check logs for errors
- [ ] Update documentation
- [ ] Close deployment ticket
- [ ] Announce completion
- [ ] Schedule post-mortem (if issues)

---

## Cost Estimation

### Development Environment

- Small K8s cluster: $100-200/month
- Managed PostgreSQL: $50-100/month
- Redis: $30-50/month
- Total: ~$200-350/month

### Staging Environment

- Medium K8s cluster: $300-500/month
- Managed PostgreSQL: $150-250/month
- Redis: $50-100/month
- Total: ~$500-850/month

### Production Environment (Small Scale)

- K8s cluster (3 nodes): $500-800/month
- Managed PostgreSQL: $300-500/month
- Redis cluster: $150-250/month
- Object storage: $50-100/month
- Load balancer: $50-100/month
- Monitoring: $100-200/month
- Total: ~$1,200-2,000/month

### Production Environment (Multi-Region)

- 3 regional K8s clusters: $1,500-2,400/month
- Multi-region database: $1,000-1,500/month
- Redis clusters: $450-750/month
- Object storage + CDN: $200-400/month
- Load balancers: $150-300/month
- Monitoring: $300-500/month
- Data transfer: $200-500/month
- Total: ~$3,800-6,350/month

**Note:** Costs scale with traffic and tenant count. LLM API costs are additional and variable based on usage.
