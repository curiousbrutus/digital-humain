# Production Deployment Guide

## Overview

This guide covers production deployment patterns for Digital Humain, including infrastructure setup, monitoring, and enterprise readiness considerations.

## Table of Contents

1. [Deployment Architectures](#deployment-architectures)
2. [Infrastructure Requirements](#infrastructure-requirements)
3. [Monitoring and Observability](#monitoring-and-observability)
4. [High Availability and Scaling](#high-availability-and-scaling)
5. [Compliance and Governance](#compliance-and-governance)

## Deployment Architectures

### Single-Node Desktop Deployment

**Use Case**: Individual workstation automation, development, testing

**Architecture**:
```
┌─────────────────────────────────────┐
│     User Workstation                │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Digital Humain Agent        │  │
│  │  - LangGraph Engine          │  │
│  │  - Local VLM (Ollama)        │  │
│  │  - GUI Actions               │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Local Resources             │  │
│  │  - Screenshots               │  │
│  │  - Logs                      │  │
│  │  - Cache                     │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Setup**:

```bash
# Install dependencies
pip install -r requirements.txt

# Start Ollama
ollama serve

# Pull models
ollama pull llava:13b-v1.6-q4_K_M

# Run agent
python -m digital_humain
```

**Recommended Specs**:
- CPU: 4+ cores
- RAM: 16GB+
- GPU: NVIDIA RTX 3060 or better (8GB+ VRAM)
- Storage: 50GB+ SSD

### Multi-Agent Server Deployment

**Use Case**: Centralized automation server for multiple agents, enterprise automation

**Architecture**:
```
┌────────────────────────────────────────────────────┐
│              Load Balancer (Nginx)                 │
└─────────────┬──────────────────────┬───────────────┘
              │                      │
    ┌─────────▼─────────┐  ┌────────▼────────┐
    │   Agent Pool 1    │  │  Agent Pool 2   │
    │                   │  │                 │
    │ ┌───────────────┐ │  │ ┌─────────────┐ │
    │ │ Agent Worker  │ │  │ │Agent Worker │ │
    │ │ (Container)   │ │  │ │(Container)  │ │
    │ └───────────────┘ │  │ └─────────────┘ │
    │                   │  │                 │
    │ ┌───────────────┐ │  │ ┌─────────────┐ │
    │ │ Agent Worker  │ │  │ │Agent Worker │ │
    │ └───────────────┘ │  │ └─────────────┘ │
    └────────┬──────────┘  └────────┬────────┘
             │                      │
             └──────────┬───────────┘
                        │
           ┌────────────▼─────────────┐
           │    Shared Services       │
           │                          │
           │  - Redis (Coordination)  │
           │  - PostgreSQL (State)    │
           │  - S3/MinIO (Artifacts) │
           │  - Prometheus/Grafana   │
           └──────────────────────────┘
```

**Docker Compose Setup**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  agent-worker:
    build: .
    image: digital-humain:latest
    runtime: runsc  # gVisor for security
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '2'
          memory: 8G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://db:5432/digital_humain
      - OLLAMA_HOST=http://ollama:11434
    volumes:
      - ./workspace:/workspace
      - ./logs:/app/logs
    networks:
      - agent-net
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - agent-net

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: digital_humain
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - agent-net

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - agent-net

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - agent-net

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    networks:
      - agent-net

volumes:
  redis-data:
  postgres-data:
  ollama-data:
  prometheus-data:
  grafana-data:

networks:
  agent-net:
    driver: bridge
```

**Deployment**:

```bash
# Build and start services
docker-compose up -d --build --scale agent-worker=4

# Check status
docker-compose ps

# View logs
docker-compose logs -f agent-worker
```

### Kubernetes Deployment

**Use Case**: Large-scale enterprise deployment, multi-tenant, global distribution

**Key Resources**:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: digital-humain-agent
  namespace: automation
spec:
  replicas: 10
  selector:
    matchLabels:
      app: digital-humain-agent
  template:
    metadata:
      labels:
        app: digital-humain-agent
    spec:
      runtimeClassName: gvisor  # Sandboxing
      
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      
      containers:
      - name: agent
        image: digital-humain:latest
        imagePullPolicy: Always
        
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
            nvidia.com/gpu: "1"
          limits:
            memory: "16Gi"
            cpu: "4"
            nvidia.com/gpu: "1"
        
        env:
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: redis-url
        
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: openrouter-key
        
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: cache
          mountPath: /app/cache
        
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: agent-workspace-pvc
      - name: cache
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: digital-humain-service
  namespace: automation
spec:
  selector:
    app: digital-humain-agent
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: digital-humain-hpa
  namespace: automation
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: digital-humain-agent
  minReplicas: 5
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Deploy to Kubernetes**:

```bash
# Create namespace
kubectl create namespace automation

# Apply configurations
kubectl apply -f k8s/

# Check rollout status
kubectl rollout status deployment/digital-humain-agent -n automation

# Scale manually
kubectl scale deployment/digital-humain-agent --replicas=20 -n automation
```

## Infrastructure Requirements

### Compute Resources

#### Development Environment
- **CPU**: 4 cores
- **RAM**: 16GB
- **GPU**: Optional (CPU inference possible but slow)
- **Storage**: 20GB

#### Production Environment (Per Agent)
- **CPU**: 2-4 cores
- **RAM**: 8-16GB
- **GPU**: NVIDIA with 8GB+ VRAM (for local VLM)
- **Storage**: 50GB SSD

#### High-Scale Production (100+ Agents)
- **CPU**: 200+ cores (distributed)
- **RAM**: 1TB+ (distributed)
- **GPU**: 20-50 NVIDIA A100 or similar
- **Storage**: 10TB+ (NFS/S3)

### Network Requirements

- **Bandwidth**: 100 Mbps+ per agent (for cloud VLM)
- **Latency**: <50ms to cloud providers (if hybrid mode)
- **Firewall**:
  - Outbound HTTPS (443) to LLM providers
  - Internal ports for coordination (Redis, PostgreSQL)

### Storage Requirements

- **Screenshots**: ~10MB per task (configurable retention)
- **Logs**: ~100MB per day per agent
- **Model Cache**: 5-50GB depending on models
- **State Database**: 1-10GB for checkpointing

## Monitoring and Observability

### Metrics to Track

#### Agent Performance

```python
# digital_humain/utils/metrics.py

from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# Define metrics
task_counter = Counter(
    'digital_humain_tasks_total',
    'Total number of tasks executed',
    ['agent_name', 'status']
)

task_duration = Histogram(
    'digital_humain_task_duration_seconds',
    'Task execution duration',
    ['agent_name']
)

action_counter = Counter(
    'digital_humain_actions_total',
    'Total number of actions executed',
    ['action_type', 'success']
)

tool_cache_hits = Counter(
    'digital_humain_cache_hits_total',
    'Tool cache hits'
)

tool_cache_misses = Counter(
    'digital_humain_cache_misses_total',
    'Tool cache misses'
)

llm_latency = Histogram(
    'digital_humain_llm_latency_seconds',
    'LLM inference latency',
    ['provider', 'model']
)

active_agents = Gauge(
    'digital_humain_active_agents',
    'Number of active agents'
)

def track_task_execution(func):
    """Decorator to track task execution metrics."""
    @wraps(func)
    def wrapper(self, task, *args, **kwargs):
        start_time = time.time()
        agent_name = self.config.name
        
        try:
            result = func(self, task, *args, **kwargs)
            
            status = 'success' if not result.get('error') else 'failed'
            task_counter.labels(agent_name=agent_name, status=status).inc()
            
            duration = time.time() - start_time
            task_duration.labels(agent_name=agent_name).observe(duration)
            
            return result
        
        except Exception as e:
            task_counter.labels(agent_name=agent_name, status='error').inc()
            raise
    
    return wrapper
```

#### System Health

- **CPU Utilization**: <80% average
- **Memory Usage**: <90% of available
- **GPU Utilization**: 60-90% (optimal)
- **Disk I/O**: Monitor for bottlenecks
- **Network**: Monitor API call latency

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'digital-humain-agents'
    static_configs:
      - targets: ['agent-worker:8000']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts.yml'
```

### Alert Rules

```yaml
# monitoring/alerts.yml
groups:
  - name: agent_alerts
    interval: 30s
    rules:
      - alert: HighTaskFailureRate
        expr: |
          rate(digital_humain_tasks_total{status="failed"}[5m]) /
          rate(digital_humain_tasks_total[5m]) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High task failure rate"
          description: "Agent {{ $labels.agent_name }} has >20% task failure rate"
      
      - alert: HighMemoryUsage
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /
          node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage >90% for 5 minutes"
      
      - alert: LLMHighLatency
        expr: |
          histogram_quantile(0.95, rate(digital_humain_llm_latency_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High LLM latency"
          description: "95th percentile LLM latency >10s"
```

### Grafana Dashboards

**Key Dashboard Panels**:

1. **Task Throughput**: Tasks per second
2. **Success Rate**: Percentage of successful tasks
3. **Average Task Duration**: Time to complete tasks
4. **Action Breakdown**: Distribution of action types
5. **Cache Hit Rate**: Efficiency of tool caching
6. **LLM Latency**: Inference time distribution
7. **Resource Utilization**: CPU, Memory, GPU usage
8. **Error Rate**: Failures over time

```json
// monitoring/dashboards/agent-overview.json (excerpt)
{
  "dashboard": {
    "title": "Digital Humain - Agent Overview",
    "panels": [
      {
        "title": "Task Throughput",
        "targets": [
          {
            "expr": "rate(digital_humain_tasks_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Success Rate",
        "targets": [
          {
            "expr": "rate(digital_humain_tasks_total{status=\"success\"}[5m]) / rate(digital_humain_tasks_total[5m])"
          }
        ],
        "type": "singlestat"
      }
    ]
  }
}
```

### Logging Best Practices

```python
# Configure structured logging
from loguru import logger
import sys
import json

# Remove default handler
logger.remove()

# Add structured JSON logging for production
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    serialize=True  # JSON output
)

# Add file logging with rotation
logger.add(
    "logs/agent_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    compression="gz",
    level="DEBUG"
)

# Log audit events
def log_audit_event(event_type: str, details: dict):
    """Log security and compliance audit events."""
    logger.bind(audit=True).info(json.dumps({
        "event_type": event_type,
        "details": details,
        "timestamp": time.time()
    }))
```

## High Availability and Scaling

### State Management

**Use LangGraph Checkpointing**:

```python
from langgraph.checkpoint.postgres import PostgresCheckpoint

# Configure checkpointer
checkpointer = PostgresCheckpoint(
    connection_string="postgresql://user:pass@db:5432/digital_humain"
)

# Build graph with checkpointing
workflow = StateGraph(AgentState)
# ... add nodes ...
graph = workflow.compile(checkpointer=checkpointer)

# Run with thread_id for resumable execution
result = graph.invoke(
    state,
    config={
        "thread_id": task_id,
        "recursion_limit": 50
    }
)

# Resume on failure
if result.get('error'):
    # Can resume from last checkpoint
    resumed_result = graph.invoke(
        state,
        config={"thread_id": task_id}
    )
```

### Load Balancing Strategies

#### Round-Robin (Simple)

```python
class AgentPool:
    """Simple round-robin agent pool."""
    
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
        self.current_index = 0
    
    def get_agent(self) -> BaseAgent:
        """Get next agent in rotation."""
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent
```

#### Least-Loaded (Advanced)

```python
class LoadAwareAgentPool:
    """Agent pool with load awareness."""
    
    def __init__(self, agents: List[BaseAgent]):
        self.agents = agents
        self.agent_loads = {agent.config.name: 0 for agent in agents}
    
    def get_agent(self) -> BaseAgent:
        """Get least loaded agent."""
        agent_name = min(self.agent_loads, key=self.agent_loads.get)
        agent = next(a for a in self.agents if a.config.name == agent_name)
        self.agent_loads[agent_name] += 1
        return agent
    
    def release_agent(self, agent: BaseAgent):
        """Mark agent as available."""
        self.agent_loads[agent.config.name] -= 1
```

### Horizontal Scaling with Ray

```python
# Optional: Use Ray for distributed agent execution
import ray

ray.init(address='auto')  # Connect to Ray cluster

@ray.remote(num_gpus=1)
class DistributedAgent:
    """Ray actor for distributed agent execution."""
    
    def __init__(self, config: AgentConfig):
        self.agent = DesktopAutomationAgent(config, ...)
    
    def execute_task(self, task: str):
        return self.agent.run(task)

# Create agent pool
agents = [DistributedAgent.remote(config) for _ in range(10)]

# Execute tasks in parallel
results = ray.get([
    agent.execute_task.remote(task)
    for agent, task in zip(agents, tasks)
])
```

## Compliance and Governance

### Data Governance Framework

**Principles**:
1. **Data Minimization**: Collect only necessary data
2. **Purpose Limitation**: Use data only for stated purposes
3. **Storage Limitation**: Retain data only as long as needed
4. **Integrity and Confidentiality**: Protect data from unauthorized access

**Implementation**:

```python
# digital_humain/utils/governance.py

from enum import Enum
from typing import Optional
import hashlib

class DataClassification(Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class DataGovernancePolicy:
    """Enforce data governance policies."""
    
    def __init__(self):
        self.retention_days = {
            DataClassification.PUBLIC: 90,
            DataClassification.INTERNAL: 30,
            DataClassification.CONFIDENTIAL: 7,
            DataClassification.RESTRICTED: 1
        }
    
    def classify_data(self, data: str) -> DataClassification:
        """Classify data based on content."""
        data_lower = data.lower()
        
        # Restricted data patterns
        if any(pattern in data_lower for pattern in [
            'ssn', 'social security', 'password', 'api_key',
            'credit card', 'medical record'
        ]):
            return DataClassification.RESTRICTED
        
        # Confidential patterns
        if any(pattern in data_lower for pattern in [
            'salary', 'financial', 'private'
        ]):
            return DataClassification.CONFIDENTIAL
        
        return DataClassification.INTERNAL
    
    def anonymize_pii(self, text: str) -> str:
        """Anonymize personally identifiable information."""
        import re
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        return text
    
    def hash_sensitive_data(self, data: str) -> str:
        """One-way hash for sensitive data."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(Enum):
    """User roles."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"

class Permission(Enum):
    """System permissions."""
    EXECUTE_TASK = "execute_task"
    VIEW_LOGS = "view_logs"
    CONFIGURE_AGENT = "configure_agent"
    MANAGE_USERS = "manage_users"

ROLE_PERMISSIONS = {
    Role.ADMIN: [Permission.EXECUTE_TASK, Permission.VIEW_LOGS, 
                 Permission.CONFIGURE_AGENT, Permission.MANAGE_USERS],
    Role.OPERATOR: [Permission.EXECUTE_TASK, Permission.VIEW_LOGS],
    Role.VIEWER: [Permission.VIEW_LOGS]
}

def check_permission(user_role: Role, required_permission: Permission) -> bool:
    """Check if role has required permission."""
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])
```

### Audit Trail

```python
def create_audit_log(
    user: str,
    action: str,
    resource: str,
    result: str,
    details: Optional[dict] = None
):
    """Create audit log entry."""
    log_entry = {
        "timestamp": time.time(),
        "user": user,
        "action": action,
        "resource": resource,
        "result": result,
        "details": details or {},
        "ip_address": get_client_ip()  # If applicable
    }
    
    # Store in database
    store_audit_log(log_entry)
    
    # Also log for immediate visibility
    log_audit_event("user_action", log_entry)
```

### Compliance Checklists

#### GDPR Compliance
- [ ] Data processing agreements in place
- [ ] Privacy policy covers automated processing
- [ ] User consent obtained for data processing
- [ ] Right to erasure implemented
- [ ] Data portability supported
- [ ] Breach notification procedures defined

#### HIPAA Compliance (if handling PHI)
- [ ] Business Associate Agreement (BAA) with vendors
- [ ] Encryption at rest and in transit
- [ ] Access controls (RBAC) implemented
- [ ] Audit logs maintained
- [ ] Security risk assessment completed
- [ ] Incident response plan documented

#### SOC 2 Compliance
- [ ] Security policies documented
- [ ] Change management process defined
- [ ] Monitoring and logging configured
- [ ] Vendor management process
- [ ] Regular security reviews scheduled
- [ ] Disaster recovery plan tested

## Quick Start Checklist

Before going to production:

- [ ] Security hardening complete (see [SECURITY.md](SECURITY.md))
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery tested
- [ ] Performance benchmarks meet requirements
- [ ] Compliance requirements validated
- [ ] Documentation complete
- [ ] Incident response procedures defined
- [ ] Load testing completed
- [ ] Failover scenarios tested
- [ ] Runbooks created for common issues

## Support

For deployment assistance:
- Documentation: [docs/README.md](README.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Security: [SECURITY.md](SECURITY.md)
- VLM Optimization: [VLM_OPTIMIZATION.md](VLM_OPTIMIZATION.md)
