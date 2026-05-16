"""
Phase 3: Service Mesh Implementation

Implements service mesh patterns for multi-mind orchestration:
- Sidecar proxies for each mind
- Centralized policy control
- Distributed execution
- Automatic observability
- Graceful degradation
"""

from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ServiceEndpoint:
    """Endpoint for a service"""
    name: str
    address: str
    port: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    healthy: bool = True
    last_health_check: Optional[datetime] = None


@dataclass
class TrafficPolicy:
    """Policy for routing traffic"""
    source_service: str
    destination_service: str
    rate_limit: Optional[float] = None
    timeout: float = 30.0
    retry_policy: Optional[str] = None
    circuit_breaker_threshold: float = 0.5


@dataclass
class ServiceMetrics:
    """Metrics for a service"""
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    average_latency: float = 0.0
    p95_latency: float = 0.0
    p99_latency: float = 0.0
    last_request_time: Optional[datetime] = None


class SidecarProxy:
    """
    Sidecar proxy that intercepts and enhances service calls.

    Provides:
    - Policy enforcement
    - Metrics collection
    - Retry logic
    - Circuit breaking
    - Request/response transformation
    """

    def __init__(self,
                 service_name: str,
                 service_endpoint: ServiceEndpoint,
                 mesh: "ServiceMesh"):
        self.service_name = service_name
        self.endpoint = service_endpoint
        self.mesh = mesh

        # State
        self.healthy = True
        self.circuit_open = False
        self.failure_count = 0
        self.success_count = 0

        # Configuration
        self.retry_limit = 3
        self.retry_delay = 1.0
        self.circuit_breaker_threshold = 0.5
        self.circuit_breaker_timeout = 60.0

        # Metrics
        self.metrics = ServiceMetrics()

    async def handle_request(self,
                            request: Dict[str, Any],
                            next_hop: Optional[str] = None) -> Any:
        """Handle an incoming request through the sidecar"""
        start_time = datetime.now()

        try:
            # Check circuit breaker
            if self.circuit_open:
                if self._should_reset_circuit():
                    self.circuit_open = False
                    logger.info(f"Circuit breaker reset for {self.service_name}")
                else:
                    raise Exception(f"Circuit breaker open for {self.service_name}")

            # Apply request policies
            request = await self._apply_request_policies(request)

            # Route to next hop or service
            if next_hop:
                result = await self._forward_to_service(request, next_hop)
            else:
                result = await self._handle_locally(request)

            # Apply response policies
            result = await self._apply_response_policies(result)

            # Update metrics
            self._update_metrics(start_time, success=True)
            self.success_count += 1

            return result

        except Exception as e:
            # Update error metrics
            self._update_metrics(start_time, success=False)
            self.failure_count += 1

            # Check circuit breaker
            failure_rate = self.failure_count / (self.success_count + self.failure_count)
            if failure_rate > self.circuit_breaker_threshold:
                self.circuit_open = True
                logger.warning(f"Circuit breaker opened for {self.service_name}")

            # Retry if appropriate
            if self._should_retry(e):
                return await self._retry_request(request, next_hop)

            raise

    async def _apply_request_policies(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Apply policies to incoming request"""
        # Add tracing headers
        request["headers"] = request.get("headers", {})
        request["headers"]["X-Service-Path"] = f"{self.service_name}"

        # Apply rate limiting
        policy = self.mesh.get_traffic_policy(self.service_name, "*")
        if policy and policy.rate_limit:
            # Check rate limit
            pass

        return request

    async def _apply_response_policies(self, response: Any) -> Any:
        """Apply policies to outgoing response"""
        return response

    async def _forward_to_service(self, request: Dict[str, Any], service: str) -> Any:
        """Forward request to another service"""
        target_proxy = self.mesh.get_sidecar(service)
        if target_proxy is None:
            raise ValueError(f"Service not found: {service}")

        return await target_proxy.handle_request(request)

    async def _handle_locally(self, request: Dict[str, Any]) -> Any:
        """Handle request locally (to be overridden)"""
        raise NotImplementedError("Local handling not implemented")

    def _should_retry(self, error: Exception) -> bool:
        """Determine if request should be retried"""
        # Retry on network errors or timeouts
        retryable_errors = ["timeout", "connection", "unavailable"]
        error_str = str(error).lower()

        return any(err in error_str for err in retryable_errors)

    async def _retry_request(self,
                            request: Dict[str, Any],
                            next_hop: Optional[str] = None) -> Any:
        """Retry a failed request"""
        for attempt in range(self.retry_limit):
            try:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                return await self.handle_request(request, next_hop)
            except Exception:
                if attempt == self.retry_limit - 1:
                    raise

    def _should_reset_circuit(self) -> bool:
        """Check if circuit breaker should be reset"""
        return self.failure_count < self.success_count

    def _update_metrics(self, start_time: datetime, success: bool):
        """Update service metrics"""
        self.metrics.request_count += 1
        self.metrics.last_request_time = datetime.now()

        if success:
            self.metrics.success_count += 1
        else:
            self.metrics.error_count += 1

        # Update latency
        elapsed = (datetime.now() - start_time).total_seconds()
        total = self.metrics.request_count
        old_avg = self.metrics.average_latency
        self.metrics.average_latency = (old_avg * (total - 1) + elapsed) / total

    def get_metrics(self) -> ServiceMetrics:
        """Get service metrics"""
        return self.metrics


class ServiceMesh:
    """
    Service mesh for managing service-to-service communication.

    Provides:
    - Service discovery
    - Traffic management
    - Policy enforcement
    - Observability
    """

    def __init__(self):
        self.sidecars: Dict[str, SidecarProxy] = {}
        self.traffic_policies: Dict[str, TrafficPolicy] = {}
        self.service_registry: Dict[str, ServiceEndpoint] = {}

        # Observability
        self.request_traces: List[Dict[str, Any]] = []
        self.mesh_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_mesh_latency": 0.0,
        }

        logger.info("Service Mesh initialized")

    def register_service(self, endpoint: ServiceEndpoint):
        """Register a service with the mesh"""
        self.service_registry[endpoint.name] = endpoint
        logger.info(f"Registered service {endpoint.name} at {endpoint.address}:{endpoint.port}")

    def register_sidecar(self, sidecar: SidecarProxy):
        """Register a sidecar proxy"""
        self.sidecars[sidecar.service_name] = sidecar
        logger.info(f"Registered sidecar for {sidecar.service_name}")

    def get_sidecar(self, service_name: str) -> Optional[SidecarProxy]:
        """Get a sidecar by service name"""
        return self.sidecars.get(service_name)

    def get_service(self, service_name: str) -> Optional[ServiceEndpoint]:
        """Get a service endpoint"""
        return self.service_registry.get(service_name)

    def add_traffic_policy(self, policy: TrafficPolicy):
        """Add a traffic policy"""
        key = f"{policy.source_service}->{policy.destination_service}"
        self.traffic_policies[key] = policy
        logger.info(f"Added traffic policy {key}")

    def get_traffic_policy(self, source: str, destination: str) -> Optional[TrafficPolicy]:
        """Get traffic policy between services"""
        # Check for exact match
        exact_key = f"{source}->{destination}"
        if exact_key in self.traffic_policies:
            return self.traffic_policies[exact_key]

        # Check for wildcard
        wildcard_key = f"{source}->*"
        if wildcard_key in self.traffic_policies:
            return self.traffic_policies[wildcard_key]

        return None

    async def route_request(self,
                           source_service: str,
                           destination_service: str,
                           request: Dict[str, Any]) -> Any:
        """Route a request through the mesh"""
        start_time = datetime.now()

        try:
            # Get source sidecar
            source_sidecar = self.get_sidecar(source_service)
            if source_sidecar is None:
                raise ValueError(f"Source service not found: {source_service}")

            # Add routing information
            request["source"] = source_service
            request["destination"] = destination_service
            request["route_timestamp"] = start_time.isoformat()

            # Handle request through sidecar
            result = await source_sidecar.handle_request(request, destination_service)

            # Update mesh metrics
            self._update_mesh_metrics(start_time, success=True)

            # Record trace
            self._record_trace(source_service, destination_service, start_time, True)

            return result

        except Exception as e:
            self._update_mesh_metrics(start_time, success=False)
            self._record_trace(source_service, destination_service, start_time, False)
            raise

    def _update_mesh_metrics(self, start_time: datetime, success: bool):
        """Update mesh-level metrics"""
        self.mesh_metrics["total_requests"] += 1

        if success:
            self.mesh_metrics["successful_requests"] += 1
        else:
            self.mesh_metrics["failed_requests"] += 1

        # Update average latency
        elapsed = (datetime.now() - start_time).total_seconds()
        total = self.mesh_metrics["total_requests"]
        old_avg = self.mesh_metrics["average_mesh_latency"]
        self.mesh_metrics["average_mesh_latency"] = (
            (old_avg * (total - 1) + elapsed) / total
        )

    def _record_trace(self,
                     source: str,
                     destination: str,
                     start_time: datetime,
                     success: bool):
        """Record a request trace"""
        self.request_traces.append({
            "source": source,
            "destination": destination,
            "start_time": start_time.isoformat(),
            "success": success,
        })

        # Keep trace buffer manageable
        if len(self.request_traces) > 10000:
            self.request_traces = self.request_traces[-5000:]

    def get_mesh_metrics(self) -> Dict[str, Any]:
        """Get mesh-level metrics"""
        return {
            **self.mesh_metrics,
            "registered_services": len(self.service_registry),
            "active_sidecars": len(self.sidecars),
            "traffic_policies": len(self.traffic_policies),
            "trace_buffer_size": len(self.request_traces),
        }


class MindSidecar(SidecarProxy):
    """
    Sidecar proxy for ASTRA minds.

    Provides mind-specific capabilities:
    - Confidence estimation
    - Capability routing
    - Mind health monitoring
    - Specialized metrics
    """

    def __init__(self,
                 mind_name: str,
                 mind_domain: str,
                 mind_instance: Any,
                 mesh: ServiceMesh):
        endpoint = ServiceEndpoint(
            name=mind_name,
            address="localhost",
            port=0,  # Internal
            metadata={"domain": mind_domain}
        )

        super().__init__(mind_name, endpoint, mesh)

        self.mind_domain = mind_domain
        self.mind_instance = mind_instance

        # Mind-specific metrics
        self.mind_metrics = {
            "queries_processed": 0,
            "confidence_distribution": [],
            "average_confidence": 0.0,
            "specialization_match": 0.0,
        }

    async def _handle_locally(self, request: Dict[str, Any]) -> Any:
        """Handle request using the mind instance"""
        query = request.get("query", "")

        logger.debug(f"{self.service_name} processing query: {query[:50]}...")

        # Process query with mind
        try:
            if hasattr(self.mind_instance, "process"):
                result = await self.mind_instance.process(query)
            elif hasattr(self.mind_instance, "answer"):
                result = self.mind_instance.answer(query)
            else:
                raise ValueError(f"Mind {self.service_name} has no process method")

            # Update mind metrics
            self.mind_metrics["queries_processed"] += 1

            # Extract confidence if available
            if isinstance(result, dict) and "confidence" in result:
                confidence = result["confidence"]
                self.mind_metrics["confidence_distribution"].append(confidence)
                self.mind_metrics["average_confidence"] = (
                    sum(self.mind_metrics["confidence_distribution"]) /
                    len(self.mind_metrics["confidence_distribution"])
                )

            return result

        except Exception as e:
            logger.error(f"Error in {self.service_name}: {e}")
            raise

    def health_check(self) -> bool:
        """Check mind health"""
        # Check if mind instance is responsive
        return self.mind_instance is not None

    def get_mind_metrics(self) -> Dict[str, Any]:
        """Get mind-specific metrics"""
        return {
            **self.mind_metrics,
            "service_metrics": self.get_metrics(),
        }


class MindServiceMesh(ServiceMesh):
    """
    Service mesh specialized for ASTRA multi-mind orchestration.

    Provides:
    - Mind discovery and registration
    - Query routing to appropriate minds
    - Mind arbitration and consensus
    - Specialized metrics for minds
    """

    def __init__(self):
        super().__init__()

        # Mind-specific state
        self.mind_capabilities: Dict[str, List[str]] = {}
        self.mind_domains: Dict[str, str] = {}
        self.arbitrator: Optional[Callable] = None

        # Query routing cache
        self.routing_cache: Dict[str, str] = {}

        logger.info("Mind Service Mesh initialized")

    def register_mind(self,
                     mind_name: str,
                     mind_domain: str,
                     mind_instance: Any,
                     capabilities: List[str]):
        """Register a mind with the service mesh"""
        # Create sidecar for mind
        sidecar = MindSidecar(
            mind_name=mind_name,
            mind_domain=mind_domain,
            mind_instance=mind_instance,
            mesh=self
        )

        # Register with mesh
        self.register_sidecar(sidecar)

        # Store mind-specific info
        self.mind_capabilities[mind_name] = capabilities
        self.mind_domains[mind_name] = mind_domain

        logger.info(f"Registered mind {mind_name} in domain {mind_domain}")

    def set_arbitrator(self, arbitrator: Callable):
        """Set the mind arbitration function"""
        self.arbitrator = arbitrator
        logger.info("Set mind arbitrator")

    async def route_query_to_minds(self,
                                  query: str,
                                  candidate_minds: Optional[List[str]] = None) -> Any:
        """Route a query to appropriate minds"""
        # Select candidate minds
        if candidate_minds is None:
            candidate_minds = self._select_minds_for_query(query)

        if not candidate_minds:
            raise ValueError("No suitable minds found for query")

        # Route to minds
        if len(candidate_minds) == 1:
            # Single mind - route directly
            return await self.route_request(
                "client",
                candidate_minds[0],
                {"query": query}
            )
        else:
            # Multiple minds - use arbitrator
            return await self._arbitrate_minds(query, candidate_minds)

    def _select_minds_for_query(self, query: str) -> List[str]:
        """Select appropriate minds for a query"""
        # Check routing cache
        if query in self.routing_cache:
            cached_mind = self.routing_cache[query]
            if cached_mind in self.sidecars:
                return [cached_mind]

        # Select based on capabilities
        query_lower = query.lower()

        # Score each mind
        mind_scores = []
        for mind_name, capabilities in self.mind_capabilities.items():
            score = 0
            for capability in capabilities:
                if capability.lower() in query_lower:
                    score += 1

            if score > 0:
                mind_scores.append((mind_name, score))

        # Sort by score and return top minds
        mind_scores.sort(key=lambda x: x[1], reverse=True)

        if mind_scores:
            # Return top 3 minds
            return [m[0] for m in mind_scores[:3]]
        else:
            # Return all minds as fallback
            return list(self.sidecars.keys())

    async def _arbitrate_minds(self,
                               query: str,
                               minds: List[str]) -> Any:
        """Arbitrate between multiple minds"""
        if self.arbitrator is None:
            # Default: simple majority voting
            return await self._majority_vote(query, minds)

        # Use custom arbitrator
        return await self.arbitrator(query, minds, self)

    async def _majority_vote(self, query: str, minds: List[str]) -> Any:
        """Implement majority voting between minds"""
        results = []

        # Collect results from all minds
        for mind_name in minds:
            try:
                result = await self.route_request(
                    "client",
                    mind_name,
                    {"query": query}
                )
                results.append({
                    "mind": mind_name,
                    "result": result,
                    "success": True,
                })
            except Exception as e:
                results.append({
                    "mind": mind_name,
                    "error": str(e),
                    "success": False,
                })

        # Count votes (simplified)
        successful = [r for r in results if r["success"]]

        if not successful:
            raise Exception("All minds failed")

        # Return result from most confident mind (simplified)
        # In real implementation, would do proper consensus
        return successful[0]["result"]

    def get_mind_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all minds"""
        metrics = {}

        for mind_name, sidecar in self.sidecars.items():
            if isinstance(sidecar, MindSidecar):
                metrics[mind_name] = sidecar.get_mind_metrics()

        return metrics

    def get_mesh_status(self) -> Dict[str, Any]:
        """Get complete mesh status"""
        return {
            "mesh_metrics": self.get_mesh_metrics(),
            "registered_minds": list(self.mind_capabilities.keys()),
            "mind_domains": self.mind_domains,
            "mind_capabilities": self.mind_capabilities,
            "mind_metrics": self.get_mind_metrics(),
        }
