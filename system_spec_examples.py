EXAMPLES = {

    "code_impl_plan": {
        "title": "Auth — JWT Refresh Token Rotation",
        "description": "Implementation plan for adding refresh token rotation to the auth module. Green nodes are new; amber nodes are modified. Click any node to see its signature and code.",
        "nodes": [
            {
                "id": "client",
                "label": "API Client",
                "kind": "external",
                "description": "Caller of the auth endpoints — a web or mobile client."
            },
            {
                "id": "auth_router",
                "label": "auth_router.py",
                "kind": "file",
                "description": "FastAPI router for /auth/* endpoints. Registers login and the new token refresh route.",
                "file_path": "src/auth/auth_router.py",
                "status": "modified",
                "tech": "Python",
                "signature": "router = APIRouter(prefix='/auth')",
                "code_snippet": "router = APIRouter(prefix='/auth')\n\n@router.post('/login')\nasync def login(creds: LoginRequest, db: Session = Depends(get_db)):\n    user = authenticate_user(db, creds.username, creds.password)\n    if not user:\n        raise HTTPException(status_code=401, detail='Bad credentials')\n    return issue_token_pair(user)\n\n@router.post('/refresh')          # NEW endpoint\nasync def refresh(body: RefreshRequest, db: Session = Depends(get_db)):\n    return rotate_refresh_token(db, body.refresh_token)",
                "previous_code_snippet": "router = APIRouter(prefix='/auth')\n\n@router.post('/login')\nasync def login(creds: LoginRequest, db: Session = Depends(get_db)):\n    user = authenticate_user(db, creds.username, creds.password)\n    if not user:\n        raise HTTPException(status_code=401, detail='Bad credentials')\n    access_token = create_access_token(user.id)\n    return {'access_token': access_token}"
            },
            {
                "id": "issue_token_pair",
                "label": "issue_token_pair()",
                "kind": "function",
                "description": "Creates both an access token and a refresh token, persists the refresh token to the DB, and returns both to the caller.",
                "file_path": "src/auth/tokens.py",
                "status": "added",
                "tech": "Python",
                "signature": "def issue_token_pair(user: User) -> TokenPair",
                "code_snippet": "def issue_token_pair(user: User) -> TokenPair:\n    access  = create_access_token(user.id)\n    refresh = secrets.token_urlsafe(48)\n    db.add(RefreshToken(\n        user_id=user.id,\n        token=hash_token(refresh),\n        expires_at=utcnow() + REFRESH_TTL,\n    ))\n    db.commit()\n    return TokenPair(access_token=access, refresh_token=refresh)"
            },
            {
                "id": "rotate_refresh_token",
                "label": "rotate_refresh_token()",
                "kind": "function",
                "description": "Validates the incoming refresh token, deletes it (single-use), issues a new token pair. Raises 401 if the token is unknown or expired.",
                "file_path": "src/auth/tokens.py",
                "status": "added",
                "tech": "Python",
                "signature": "def rotate_refresh_token(db: Session, raw_token: str) -> TokenPair",
                "code_snippet": "def rotate_refresh_token(db: Session, raw_token: str) -> TokenPair:\n    record = db.query(RefreshToken).filter_by(\n        token=hash_token(raw_token)\n    ).first()\n    if not record or record.expires_at < utcnow():\n        raise HTTPException(status_code=401, detail='Invalid refresh token')\n    user = db.get(User, record.user_id)\n    db.delete(record)   # single-use: revoke immediately\n    db.commit()\n    return issue_token_pair(user)"
            },
            {
                "id": "create_access_token",
                "label": "create_access_token()",
                "kind": "function",
                "description": "Encodes a short-lived JWT. Unchanged — called by the new issue_token_pair helper.",
                "file_path": "src/auth/tokens.py",
                "status": "stable",
                "tech": "Python",
                "signature": "def create_access_token(user_id: int) -> str"
            },
            {
                "id": "hash_token",
                "label": "hash_token()",
                "kind": "function",
                "description": "SHA-256 hashes a raw token string before DB storage so plaintext tokens are never persisted.",
                "file_path": "src/auth/tokens.py",
                "status": "added",
                "tech": "Python",
                "signature": "def hash_token(raw: str) -> str",
                "code_snippet": "def hash_token(raw: str) -> str:\n    return hashlib.sha256(raw.encode()).hexdigest()"
            },
            {
                "id": "refresh_token_model",
                "label": "RefreshToken",
                "kind": "class",
                "description": "SQLAlchemy model for the refresh_tokens table. Each row is a single-use token tied to a user.",
                "file_path": "src/auth/models.py",
                "status": "added",
                "tech": "Python",
                "signature": "class RefreshToken(Base)",
                "code_snippet": "class RefreshToken(Base):\n    __tablename__ = 'refresh_tokens'\n    id         = Column(Integer, primary_key=True)\n    user_id    = Column(Integer, ForeignKey('users.id'), nullable=False)\n    token      = Column(String(64), unique=True, nullable=False)  # SHA-256 hex\n    expires_at = Column(DateTime, nullable=False)\n    created_at = Column(DateTime, default=utcnow)"
            },
            {
                "id": "db",
                "label": "refresh_tokens table",
                "kind": "db",
                "tech": "PostgreSQL",
                "description": "Stores hashed refresh tokens. Old tokens are deleted on use (rotation) or by a nightly cleanup job."
            }
        ],
        "edges": [
            {"from": "client",              "to": "auth_router",         "kind": "calls",   "label": "POST /auth/login"},
            {"from": "client",              "to": "auth_router",         "kind": "calls",   "label": "POST /auth/refresh"},
            {"from": "auth_router",         "to": "issue_token_pair",    "kind": "calls",   "label": "on login"},
            {"from": "auth_router",         "to": "rotate_refresh_token","kind": "calls",   "label": "on refresh"},
            {"from": "issue_token_pair",    "to": "create_access_token", "kind": "calls"},
            {"from": "issue_token_pair",    "to": "hash_token",          "kind": "calls"},
            {"from": "issue_token_pair",    "to": "db",                  "kind": "writes",  "label": "INSERT token"},
            {"from": "rotate_refresh_token","to": "hash_token",          "kind": "calls"},
            {"from": "rotate_refresh_token","to": "db",                  "kind": "reads",   "label": "lookup token"},
            {"from": "rotate_refresh_token","to": "db",                  "kind": "writes",  "label": "DELETE token"},
            {"from": "rotate_refresh_token","to": "issue_token_pair",    "kind": "calls",   "label": "re-issue"},
            {"from": "refresh_token_model", "to": "db",                  "kind": "owns"},
        ],
        "groups": [
            {"id": "router_file", "label": "auth_router.py", "kind": "package", "members": ["auth_router"]},
            {"id": "tokens_file", "label": "tokens.py",      "kind": "package", "members": ["issue_token_pair", "rotate_refresh_token", "create_access_token", "hash_token"]},
            {"id": "models_file", "label": "models.py",      "kind": "package", "members": ["refresh_token_model"]},
        ],
        "sequences": [
            {
                "id": "before",
                "label": "Before — login returns access token only",
                "steps": [
                    {"from": "client",       "to": "auth_router",      "label": "POST /auth/login"},
                    {"from": "auth_router",  "to": "create_access_token","label": "create JWT"},
                    {"from": "auth_router",  "to": "client",           "label": "{ access_token }"},
                ]
            },
            {
                "id": "after",
                "label": "After — login + refresh rotation",
                "steps": [
                    {"from": "client",              "to": "auth_router",          "label": "POST /auth/login"},
                    {"from": "auth_router",         "to": "issue_token_pair",     "label": "issue pair"},
                    {"from": "issue_token_pair",    "to": "create_access_token",  "label": "JWT"},
                    {
                        "from": "issue_token_pair", "to": "hash_token", "label": "hash refresh",
                        "example_before": "rt_8f3a1c9e2b4d5f60...",
                        "example_after": "$2b$12$KIXQeC9z7Y8x1mN3pQrS5e",
                    },
                    {"from": "issue_token_pair",    "to": "db",                   "label": "INSERT refresh_token"},
                    {"from": "auth_router",         "to": "client",               "label": "{ access_token, refresh_token }"},
                    {"from": "client",              "to": "auth_router",          "label": "POST /auth/refresh"},
                    {"from": "auth_router",         "to": "rotate_refresh_token", "label": "rotate"},
                    {"from": "rotate_refresh_token","to": "db",                   "label": "DELETE old token"},
                    {"from": "rotate_refresh_token","to": "issue_token_pair",     "label": "re-issue"},
                    {"from": "auth_router",         "to": "client",               "label": "new { access_token, refresh_token }"},
                ]
            }
        ]
    },

    "code_bug_fix": {
        "title": "Bug Fix — Cache Invalidation Race Condition",
        "description": "A race condition in the product cache allowed stale data to be served after an update. The fix adds a write-through invalidation step inside the DB transaction.",
        "nodes": [
            {
                "id": "update_product",
                "label": "update_product()",
                "kind": "function",
                "description": "Updates a product record. Previously invalidated the cache AFTER committing, creating a window where another request could repopulate the cache with stale data. Fixed by invalidating inside the transaction.",
                "file_path": "src/products/service.py",
                "line_range": [42, 61],
                "status": "modified",
                "tech": "Python",
                "signature": "def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product",
                "previous_code_snippet": "def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:\n    product = db.get(Product, product_id)\n    if not product:\n        raise NotFoundError(product_id)\n    for field, value in data.dict(exclude_unset=True).items():\n        setattr(product, field, value)\n    db.commit()\n    db.refresh(product)\n    cache.delete(f'product:{product_id}')  # BUG: too late — window exists here\n    return product",
                "code_snippet": "def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:\n    product = db.get(Product, product_id)\n    if not product:\n        raise NotFoundError(product_id)\n    for field, value in data.dict(exclude_unset=True).items():\n        setattr(product, field, value)\n    cache.delete(f'product:{product_id}')  # FIX: invalidate before commit\n    db.commit()\n    db.refresh(product)\n    return product"
            },
            {
                "id": "get_product",
                "label": "get_product()",
                "kind": "function",
                "description": "Cache-aside read. Checks cache first; on miss, loads from DB and populates cache. Unchanged.",
                "file_path": "src/products/service.py",
                "line_range": [22, 38],
                "status": "stable",
                "tech": "Python",
                "signature": "def get_product(db: Session, product_id: int) -> Product"
            },
            {
                "id": "cache_delete",
                "label": "cache.delete()",
                "kind": "function",
                "description": "Redis DEL call. Fast synchronous operation.",
                "file_path": "src/cache.py",
                "status": "stable",
                "tech": "Python"
            },
            {
                "id": "db_session",
                "label": "DB Session",
                "kind": "db",
                "tech": "PostgreSQL",
                "description": "SQLAlchemy session. db.commit() flushes and ends the transaction."
            },
            {
                "id": "cache",
                "label": "Cache",
                "kind": "db",
                "tech": "Redis",
                "description": "Product cache. Keys are 'product:{id}', TTL 5 minutes."
            },
            {
                "id": "product_router",
                "label": "product_router.py",
                "kind": "file",
                "description": "FastAPI router — calls update_product on PATCH /products/{id}. Unchanged.",
                "file_path": "src/products/product_router.py",
                "status": "stable",
                "tech": "Python"
            }
        ],
        "edges": [
            {"from": "product_router", "to": "update_product", "kind": "calls",  "label": "PATCH /products/{id}"},
            {"from": "product_router", "to": "get_product",    "kind": "calls",  "label": "GET /products/{id}"},
            {"from": "update_product", "to": "db_session",     "kind": "writes", "label": "commit"},
            {"from": "update_product", "to": "cache_delete",   "kind": "calls",  "label": "invalidate"},
            {"from": "cache_delete",   "to": "cache",          "kind": "writes", "label": "DEL key"},
            {"from": "get_product",    "to": "cache",          "kind": "reads",  "label": "GET key"},
            {"from": "get_product",    "to": "db_session",     "kind": "reads",  "label": "on miss"},
        ],
        "sequences": [
            {
                "id": "race",
                "label": "Bug — race window after commit",
                "steps": [
                    {"from": "product_router", "to": "update_product", "label": "PATCH product"},
                    {"from": "update_product", "to": "db_session",     "label": "db.commit()  ← committed"},
                    {"from": "product_router", "to": "get_product",    "label": "concurrent GET (cache miss)"},
                    {
                        "from": "get_product", "to": "db_session", "label": "load from DB → stale repopulates cache",
                        "example": '{"id": 42, "name": "Widget", "price": 9.99}  // old price, written back to cache',
                        "example_lang": "json",
                    },
                    {"from": "update_product", "to": "cache_delete",   "label": "cache.delete()  ← too late"},
                ]
            },
            {
                "id": "fixed",
                "label": "Fix — invalidate inside transaction",
                "steps": [
                    {"from": "product_router", "to": "update_product", "label": "PATCH product"},
                    {"from": "update_product", "to": "cache_delete",   "label": "cache.delete()  ← before commit"},
                    {"from": "cache_delete",   "to": "cache",          "label": "DEL product:id"},
                    {"from": "update_product", "to": "db_session",     "label": "db.commit()"},
                    {"from": "product_router", "to": "get_product",    "label": "concurrent GET"},
                    {"from": "get_product",    "to": "cache",          "label": "miss → loads fresh from DB"},
                ]
            }
        ]
    },

    "sys_microservices": {
        "title": "E-Commerce Platform — Service Architecture",
        "description": "Microservices architecture for a mid-size e-commerce platform. Each service owns its database. The API Gateway is the only public-facing entry point.",
        "nodes": [
            {"id": "client",    "label": "Web Client",        "kind": "external", "description": "React SPA served via CDN"},
            {"id": "mobile",    "label": "Mobile App",        "kind": "external", "description": "iOS/Android, talks directly to gateway"},
            {"id": "gateway",   "label": "API Gateway",       "kind": "service",  "description": "Auth, rate-limiting, routing. Only public-facing entry point.", "tech": "nginx + lua", "tags": ["critical", "public-facing"]},
            {"id": "orders",    "label": "Order Service",     "kind": "service",  "description": "Create, fulfill, cancel orders. Emits OrderPlaced events.", "tech": "Go", "owner": "fulfillment-team"},
            {"id": "inventory", "label": "Inventory Service", "kind": "service",  "description": "Tracks stock levels. Subscribes to OrderPlaced to reserve stock.", "tech": "Go", "owner": "fulfillment-team"},
            {"id": "payments",  "label": "Payment Service",   "kind": "service",  "description": "Charge and refund. Talks to Stripe.", "tech": "Node.js", "owner": "payments-team", "tags": ["pci-scope"]},
            {"id": "users",     "label": "User Service",      "kind": "service",  "description": "Profile, auth tokens, preferences.", "tech": "Python", "owner": "platform-team"},
            {"id": "notify",    "label": "Notification Svc",  "kind": "service",  "description": "Email and push. Consumes events from the bus.", "tech": "Python", "owner": "platform-team"},
            {"id": "orderdb",   "label": "Orders DB",         "kind": "db",       "tech": "PostgreSQL"},
            {"id": "invdb",     "label": "Inventory DB",      "kind": "db",       "tech": "PostgreSQL"},
            {"id": "paydb",     "label": "Payments DB",       "kind": "db",       "tech": "PostgreSQL"},
            {"id": "userdb",    "label": "Users DB",          "kind": "db",       "tech": "PostgreSQL"},
            {"id": "bus",       "label": "Event Bus",         "kind": "queue",    "description": "Async domain events (OrderPlaced, PaymentFailed, etc.)", "tech": "Kafka"},
            {"id": "stripe",    "label": "Stripe",            "kind": "external", "description": "Payment processor"},
        ],
        "edges": [
            {"from": "client",    "to": "gateway",   "kind": "calls",      "label": "HTTPS"},
            {"from": "mobile",    "to": "gateway",   "kind": "calls",      "label": "HTTPS"},
            {"from": "gateway",   "to": "orders",    "kind": "calls",      "label": "REST"},
            {"from": "gateway",   "to": "users",     "kind": "calls",      "label": "REST"},
            {"from": "gateway",   "to": "inventory", "kind": "calls",      "label": "REST"},
            {"from": "orders",    "to": "payments",  "kind": "calls",      "label": "gRPC"},
            {"from": "orders",    "to": "orderdb",   "kind": "writes",     "label": "SQL"},
            {"from": "orders",    "to": "bus",       "kind": "emits",      "label": "OrderPlaced"},
            {"from": "inventory", "to": "invdb",     "kind": "writes",     "label": "SQL"},
            {"from": "inventory", "to": "bus",       "kind": "subscribes", "async": True},
            {"from": "payments",  "to": "paydb",     "kind": "writes",     "label": "SQL"},
            {"from": "payments",  "to": "stripe",    "kind": "calls",      "label": "HTTPS"},
            {"from": "users",     "to": "userdb",    "kind": "writes",     "label": "SQL"},
            {"from": "notify",    "to": "bus",       "kind": "subscribes", "async": True},
        ],
        "groups": [
            {"id": "public",      "label": "Public Zone",    "kind": "layer",  "members": ["client", "mobile"]},
            {"id": "edge",        "label": "Edge Layer",     "kind": "layer",  "members": ["gateway"]},
            {"id": "fulfillment", "label": "Fulfillment",    "kind": "domain", "members": ["orders", "inventory", "orderdb", "invdb"]},
            {"id": "data",        "label": "Data Layer",     "kind": "layer",  "members": ["orderdb", "invdb", "paydb", "userdb"]},
        ],
        "sequences": [
            {
                "id": "place-order",
                "label": "Place Order (happy path)",
                "steps": [
                    {
                        "from": "client", "to": "gateway", "label": "POST /orders HTTPS",
                        "example": '{"items": [{"sku": "WIDGET-1", "qty": 2}], "shipping_address_id": "addr_88f3"}',
                        "example_lang": "json",
                    },
                    {"from": "gateway",   "to": "orders",    "label": "create order REST"},
                    {"from": "orders",    "to": "payments",  "label": "charge card gRPC"},
                    {"from": "payments",  "to": "paydb",     "label": "record payment SQL"},
                    {"from": "payments",  "to": "orders",    "label": "payment confirmed"},
                    {"from": "orders",    "to": "orderdb",   "label": "persist order SQL"},
                    {"from": "orders",    "to": "bus",       "label": "emit OrderPlaced"},
                    {"from": "inventory", "to": "bus",       "label": "consume OrderPlaced"},
                    {"from": "notify",    "to": "bus",       "label": "consume → send email"},
                ]
            },
            {
                "id": "user-login",
                "label": "User Login",
                "steps": [
                    {"from": "client",  "to": "gateway", "label": "POST /auth/login HTTPS"},
                    {"from": "gateway", "to": "users",   "label": "verify credentials REST"},
                    {
                        "from": "users", "to": "userdb", "label": "lookup user SQL",
                        "example": "SELECT id, password_hash FROM users WHERE email = $1",
                        "example_lang": "sql",
                    },
                    {"from": "users",   "to": "gateway", "label": "JWT + refresh token"},
                    {"from": "gateway", "to": "client",  "label": "200 OK + tokens"},
                ]
            }
        ]
    },

    "sys_event_driven": {
        "title": "Data Ingestion Pipeline",
        "description": "Event-driven pipeline for ingesting, transforming, and storing telemetry data from IoT devices.",
        "nodes": [
            {"id": "device",    "label": "IoT Device",       "kind": "external", "description": "Publishes telemetry at up to 1 Hz"},
            {"id": "ingest",    "label": "Ingest API",        "kind": "service",  "description": "Validates and fans out inbound events", "tech": "Go", "tags": ["high-throughput"]},
            {"id": "raw",       "label": "Raw Events Topic",  "kind": "queue",    "tech": "Kafka", "description": "Unprocessed events, 7-day retention"},
            {"id": "transform", "label": "Transform Worker",  "kind": "service",  "description": "Normalizes units, deduplicates, enriches with device metadata", "tech": "Python"},
            {"id": "dlq",       "label": "Dead Letter Queue", "kind": "queue",    "tech": "Kafka", "description": "Failed transform events for investigation"},
            {"id": "enriched",  "label": "Enriched Topic",    "kind": "queue",    "tech": "Kafka", "description": "Processed, ready-to-store events"},
            {"id": "loader",    "label": "Batch Loader",      "kind": "service",  "description": "Micro-batches enriched events into the warehouse", "tech": "Python"},
            {"id": "warehouse", "label": "Data Warehouse",    "kind": "db",       "tech": "BigQuery", "description": "Long-term storage, queried by analysts"},
            {"id": "stream",    "label": "Stream Processor",  "kind": "service",  "description": "Windowed aggregations for real-time dashboards", "tech": "Flink"},
            {"id": "cache",     "label": "Metrics Cache",     "kind": "db",       "tech": "Redis",    "description": "Latest aggregates, TTL 60s"},
            {"id": "api",       "label": "Dashboard API",     "kind": "service",  "description": "Serves real-time and historical metrics to the UI", "tech": "Go"},
            {"id": "ui",        "label": "Dashboard UI",      "kind": "external", "description": "Analyst-facing dashboard"},
        ],
        "edges": [
            {"from": "device",    "to": "ingest",    "kind": "calls",      "label": "HTTPS POST"},
            {"from": "ingest",    "to": "raw",       "kind": "emits",      "label": "publish"},
            {"from": "transform", "to": "raw",       "kind": "subscribes", "async": True},
            {"from": "transform", "to": "enriched",  "kind": "emits",      "label": "publish"},
            {"from": "transform", "to": "dlq",       "kind": "emits",      "label": "on error", "async": True},
            {"from": "loader",    "to": "enriched",  "kind": "subscribes", "async": True},
            {"from": "loader",    "to": "warehouse", "kind": "writes",     "label": "batch insert"},
            {"from": "stream",    "to": "enriched",  "kind": "subscribes", "async": True},
            {"from": "stream",    "to": "cache",     "kind": "writes",     "label": "aggregates"},
            {"from": "api",       "to": "cache",     "kind": "reads",      "label": "real-time"},
            {"from": "api",       "to": "warehouse", "kind": "reads",      "label": "historical"},
            {"from": "ui",        "to": "api",       "kind": "calls",      "label": "HTTPS"},
        ],
        "groups": [
            {"id": "ingestion",  "label": "Ingestion",   "kind": "layer", "members": ["ingest", "raw"]},
            {"id": "processing", "label": "Processing",  "kind": "layer", "members": ["transform", "dlq", "enriched"]},
            {"id": "storage",    "label": "Storage",     "kind": "layer", "members": ["loader", "warehouse", "stream", "cache"]},
            {"id": "serving",    "label": "Serving",     "kind": "layer", "members": ["api", "ui"]},
        ],
        "sequences": [
            {
                "id": "ingest-store",
                "label": "Ingest & Store",
                "steps": [
                    {"from": "device",    "to": "ingest",    "label": "POST /ingest HTTPS"},
                    {"from": "ingest",    "to": "raw",       "label": "publish to raw topic"},
                    {"from": "transform", "to": "raw",       "label": "consume event"},
                    {"from": "transform", "to": "enriched",  "label": "publish enriched"},
                    {"from": "loader",    "to": "enriched",  "label": "consume batch"},
                    {"from": "loader",    "to": "warehouse", "label": "batch insert"},
                    {"from": "stream",    "to": "enriched",  "label": "consume windowed"},
                    {"from": "stream",    "to": "cache",     "label": "write aggregates"},
                ]
            },
            {
                "id": "view-dashboard",
                "label": "View Dashboard",
                "steps": [
                    {"from": "ui",  "to": "api",       "label": "GET /metrics/realtime"},
                    {"from": "api", "to": "cache",     "label": "read TTL aggregates"},
                    {"from": "api", "to": "ui",        "label": "current metrics"},
                    {"from": "ui",  "to": "api",       "label": "GET /metrics/historical"},
                    {"from": "api", "to": "warehouse", "label": "BigQuery SQL"},
                    {"from": "api", "to": "ui",        "label": "time-series data"},
                ]
            }
        ]
    },

    "sys_monolith": {
        "title": "Rails Monolith — Module Architecture",
        "description": "Module-level view of a Rails monolith before a planned decomposition. Dashed edges highlight the coupling that makes decomposition hard.",
        "nodes": [
            {"id": "web",      "label": "Web Controllers",   "kind": "module",   "description": "ActionController subclasses, session handling, routing", "tech": "Rails"},
            {"id": "api",      "label": "API Controllers",   "kind": "module",   "description": "JSON API endpoints, token auth", "tech": "Rails"},
            {"id": "billing",  "label": "Billing",           "kind": "module",   "description": "Subscription management, invoicing, Stripe sync", "tech": "Ruby", "owner": "payments-team", "tags": ["decompose-candidate"]},
            {"id": "auth",     "label": "Auth",              "kind": "module",   "description": "Devise + custom RBAC, JWT issuance", "tech": "Ruby", "owner": "platform-team"},
            {"id": "notifs",   "label": "Notifications",     "kind": "module",   "description": "Email, in-app, push. Uses ActionMailer + Noticed gem", "tech": "Ruby", "tags": ["decompose-candidate"]},
            {"id": "jobs",     "label": "Background Jobs",   "kind": "module",   "description": "Sidekiq workers — renewal, digest emails, exports", "tech": "Sidekiq"},
            {"id": "reports",  "label": "Reports",           "kind": "module",   "description": "SQL-heavy reporting, CSV export", "tech": "Ruby", "tags": ["slow"]},
            {"id": "models",   "label": "ActiveRecord Models","kind": "module",  "description": "Shared data layer — User, Account, Subscription, Invoice, etc.", "tech": "Rails"},
            {"id": "db",       "label": "PostgreSQL",        "kind": "db",       "tech": "PostgreSQL 15"},
            {"id": "redis",    "label": "Redis",             "kind": "db",       "tech": "Redis 7", "description": "Sidekiq queue + session store"},
            {"id": "stripe",   "label": "Stripe",            "kind": "external"},
            {"id": "ses",      "label": "AWS SES",           "kind": "external", "description": "Email delivery"},
        ],
        "edges": [
            {"from": "web",     "to": "auth",     "kind": "depends",  "label": "before_action"},
            {"from": "web",     "to": "models",   "kind": "reads",    "label": "ActiveRecord"},
            {"from": "api",     "to": "auth",     "kind": "depends",  "label": "JWT verify"},
            {"from": "api",     "to": "models",   "kind": "reads"},
            {"from": "billing", "to": "models",   "kind": "writes",   "label": "Subscription/Invoice"},
            {"from": "billing", "to": "stripe",   "kind": "calls",    "label": "HTTPS"},
            {"from": "billing", "to": "notifs",   "kind": "calls",    "label": "payment events", "async": True},
            {"from": "auth",    "to": "models",   "kind": "reads",    "label": "User/Account"},
            {"from": "notifs",  "to": "ses",      "kind": "calls",    "label": "SMTP"},
            {"from": "notifs",  "to": "models",   "kind": "reads"},
            {"from": "jobs",    "to": "billing",  "kind": "calls",    "label": "renewal job"},
            {"from": "jobs",    "to": "notifs",   "kind": "calls",    "label": "digest job"},
            {"from": "jobs",    "to": "redis",    "kind": "reads",    "label": "queue"},
            {"from": "reports", "to": "models",   "kind": "reads",    "label": "direct SQL"},
            {"from": "models",  "to": "db",       "kind": "reads"},
        ],
        "groups": [
            {"id": "frontend",  "label": "Presentation",  "kind": "layer", "members": ["web", "api"]},
            {"id": "domain",    "label": "Domain",        "kind": "layer", "members": ["billing", "auth", "notifs", "reports"]},
            {"id": "infra",     "label": "Infrastructure","kind": "layer", "members": ["jobs", "models", "db", "redis"]},
        ]
    },

    "mixed_levels": {
        "title": "Notes API — System + Code Detail",
        "description": "A small system view (gateway, auth service, notes service, db) where the Auth Service group has a 'Code Detail' drill-down into its actual functions, including a recent fix to token verification. Demonstrates combining system-level and code-level content in one artifact.",
        "nodes": [
            {"id": "client",  "label": "Web Client",   "kind": "external", "description": "Browser SPA"},
            {"id": "gateway", "label": "API Gateway",  "kind": "service",  "description": "Routes requests, enforces auth on protected routes.", "tech": "nginx"},
            {"id": "auth",    "label": "Auth Service", "kind": "service",  "description": "Issues and verifies session tokens.", "tech": "Python", "owner": "platform-team"},
            {"id": "notes",   "label": "Notes Service","kind": "service",  "description": "CRUD for user notes. Calls Auth Service to verify tokens.", "tech": "Python", "owner": "notes-team"},
            {"id": "db",      "label": "Notes DB",     "kind": "db",       "tech": "PostgreSQL"}
        ],
        "edges": [
            {"from": "client",  "to": "gateway", "kind": "calls", "label": "HTTPS"},
            {"from": "gateway", "to": "auth",    "kind": "calls", "label": "verify token"},
            {"from": "gateway", "to": "notes",   "kind": "calls", "label": "REST"},
            {"from": "notes",   "to": "auth",    "kind": "calls", "label": "verify token"},
            {"from": "notes",   "to": "db",      "kind": "reads", "label": "SQL"},
            {"from": "notes",   "to": "db",      "kind": "writes","label": "SQL"}
        ],
        "groups": [
            {
                "id": "auth_group",
                "label": "Auth Service",
                "kind": "package",
                "members": ["auth"],
                "detail": {
                    "nodes": [
                        {"id": "verify_token", "label": "verify_token()", "kind": "function", "status": "modified", "tech": "Python", "file_path": "auth/tokens.py", "line_range": [18, 34], "description": "Verifies a session token's signature and expiry. Fixed to also check the token's revocation list, closing a window where revoked tokens were still accepted.", "signature": "def verify_token(token: str) -> User", "previous_code_snippet": "def verify_token(token: str) -> User:\n    payload = jwt.decode(token, SECRET, algorithms=[\"HS256\"])\n    if payload[\"exp\"] < time.time():\n        raise TokenExpired()\n    return User.objects.get(id=payload[\"sub\"])", "code_snippet": "def verify_token(token: str) -> User:\n    payload = jwt.decode(token, SECRET, algorithms=[\"HS256\"])\n    if payload[\"exp\"] < time.time():\n        raise TokenExpired()\n    if is_revoked(payload[\"jti\"]):\n        raise TokenRevoked()\n    return User.objects.get(id=payload[\"sub\"])"},
                        {"id": "is_revoked", "label": "is_revoked()", "kind": "function", "status": "added", "tech": "Python", "file_path": "auth/tokens.py", "line_range": [36, 39], "description": "New helper checking the Redis revocation set for a token's JTI.", "signature": "def is_revoked(jti: str) -> bool", "code_snippet": "def is_revoked(jti: str) -> bool:\n    return redis.sismember(\"revoked_tokens\", jti)"},
                        {"id": "issue_token", "label": "issue_token()", "kind": "function", "status": "stable", "tech": "Python", "file_path": "auth/tokens.py", "line_range": [1, 16], "description": "Issues a signed session token for a user.", "signature": "def issue_token(user: User) -> str", "code_snippet": "def issue_token(user: User) -> str:\n    payload = {\"sub\": user.id, \"jti\": uuid4().hex, \"exp\": time.time() + 3600}\n    return jwt.encode(payload, SECRET, algorithm=\"HS256\")"},
                        {"id": "revoke_token", "label": "revoke_token()", "kind": "function", "status": "added", "tech": "Python", "file_path": "auth/tokens.py", "line_range": [41, 43], "description": "New endpoint handler — adds a token's JTI to the revocation set on logout.", "signature": "def revoke_token(jti: str) -> None", "code_snippet": "def revoke_token(jti: str) -> None:\n    redis.sadd(\"revoked_tokens\", jti)"}
                    ],
                    "edges": [
                        {"from": "verify_token", "to": "is_revoked", "kind": "calls"},
                        {"from": "verify_token", "to": "issue_token", "kind": "depends", "label": "shares SECRET"},
                        {"from": "revoke_token", "to": "is_revoked", "kind": "depends", "label": "writes set read by"}
                    ]
                }
            }
        ]
    },
}
