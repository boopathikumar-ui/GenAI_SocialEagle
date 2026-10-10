# PRP: Team14-Roast

> Implementation blueprint for parallel agent execution

---

## METADATA

| Field | Value |
|-------|-------|
| **Product** | Team14-Roast |
| **Type** | SaaS (free consumer fun app) |
| **Version** | 1.0 |
| **Created** | 2026-10-10 |
| **Complexity** | Medium |

---

## PRODUCT OVERVIEW

**Description:** Users paste a public GitHub profile or repo link and receive a humorous, good-natured AI roast generated from public GitHub data. Roasts are stored, shareable by public link, and (post-MVP) reactable in a public gallery.

**Value Proposition:** Instant, shareable fun for developers. Viral by design through share links.

**Content Rules:** Roast code, repos, and public activity only. Never personal attributes. Intensity levels mild / medium / spicy are playful, never abusive.

**MVP Scope:**
- [ ] Register / login, including Google OAuth
- [ ] Submit GitHub profile or repo URL, get a roast
- [ ] Intensity picker (mild / medium / spicy)
- [ ] Shareable public roast link
- [ ] My roast history

**Post-MVP:** Gallery with reactions, analytics dashboard, roast battles, share-as-image card.

---

## TECH STACK

| Layer | Technology | Skill Reference |
|-------|------------|-----------------|
| Backend | FastAPI + Python 3.11+ | skills/BACKEND.md |
| Frontend | React + TypeScript + Vite | skills/FRONTEND.md |
| Database | PostgreSQL + SQLAlchemy + Alembic | skills/DATABASE.md |
| Auth | JWT + bcrypt + Google OAuth | skills/BACKEND.md |
| UI | Chakra UI + Framer Motion | skills/FRONTEND.md |
| LLM | Anthropic Claude API (`ANTHROPIC_API_KEY`, `ROAST_MODEL`) | skills/BACKEND.md |
| External | GitHub REST API (optional `GITHUB_TOKEN`) | skills/BACKEND.md |
| Testing | pytest + React Testing Library (GitHub and LLM mocked) | skills/TESTING.md |
| Deployment | Docker + GitHub Actions | skills/DEPLOYMENT.md |

---

## DATABASE MODELS

All models use TimestampMixin (`created_at`, `updated_at`).

### User
id, email (unique), hashed_password (nullable for OAuth), full_name, is_active, is_verified, is_admin, oauth_provider, created_at

### RefreshToken
id, user_id (FK User), token (unique, hashed), expires_at, revoked

### Roast
id, user_id (FK User, nullable for anonymous), github_url, github_username, target_type (profile | repo), intensity (mild | medium | spicy), roast_text, github_snapshot (JSON), is_public (bool), share_slug (unique, indexed), created_at, updated_at
Indexes: user_id, share_slug, (is_public, created_at)

### Reaction (post-MVP, model created in Phase 1)
id, roast_id (FK Roast), user_id (FK User), emoji (fire | skull | laugh | clap), created_at
Unique: (roast_id, user_id, emoji)

Relationships: User 1-N Roast, User 1-N RefreshToken, Roast 1-N Reaction.

---

## MODULES

### Module 1: Authentication
**Agents:** DATABASE-AGENT + BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Get access + refresh tokens |
| POST | /api/v1/auth/refresh | Refresh access token |
| POST | /api/v1/auth/logout | Revoke refresh token |
| GET | /api/v1/auth/me | Current user |
| PUT | /api/v1/auth/me | Update profile |
| GET | /api/v1/auth/google | Start Google OAuth (state param for CSRF) |
| GET | /api/v1/auth/google/callback | OAuth callback |

JWT: access 30 min, refresh 7 days, HS256. Rate limit on login/register.

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /login | LoginPage | LoginForm, GoogleLoginButton, GradientButton |
| /register | RegisterPage | RegisterForm |
| /profile | ProfilePage (protected) | ProfileForm |

Also: AuthContext, useAuth, authService, ProtectedRoute.

---

### Module 2: Roasts (Core)
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Services:**
- GitHubService: strict validation that host is `github.com` (SSRF prevention), parse profile vs repo, fetch public data (profile, top repos, languages, recent commit messages, README snippet), friendly errors for 404 and rate limit
- RoastService: build prompt from snapshot + intensity, call Claude API, apply content-safety guard (prompt rules + post-check), store roast, generate share_slug

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/roasts | Create roast from GitHub URL + intensity (auth optional, rate limited) |
| GET | /api/v1/roasts | List my roasts (paginated) |
| GET | /api/v1/roasts/{id} | Get one (owner) |
| DELETE | /api/v1/roasts/{id} | Delete mine |
| PATCH | /api/v1/roasts/{id} | Toggle is_public |
| GET | /api/v1/roasts/s/{slug} | Public shared roast |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| / | LandingPage | UrlInput, IntensityPicker, GradientButton, GlassCard |
| /roasts | RoastHistoryPage (protected) | RoastCard, AnimatedList |
| /roasts/:id | RoastResultPage | RoastDisplay, ShareButton, CopyButton |
| /r/:slug | SharedRoastPage | RoastDisplay |

Loading state with funny messages while the roast generates. Roast text rendered escaped, never as raw HTML.

---

### Module 3: Gallery and Reactions (post-MVP)
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/gallery | Public roasts, paginated, sort=new|top |
| POST | /api/v1/roasts/{id}/reactions | Add reaction |
| DELETE | /api/v1/roasts/{id}/reactions/{emoji} | Remove reaction |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /gallery | GalleryPage | RoastCard, ReactionBar |

---

### Module 4: Dashboard (post-MVP)
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/dashboard/stats | Roasts per day, top languages, intensity split, reactions received |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /dashboard | DashboardPage (protected) | StatCard, charts |
| /settings | SettingsPage (protected) | SettingsForm |

---

## PHASE EXECUTION PLAN

**Phase 1: Foundation (4 agents in parallel)**
- DATABASE-AGENT: all 4 models, base mixins, database.py, Alembic initial migration
- BACKEND-AGENT: main.py, config.py, dependencies.py, exceptions.py, rate limiting setup, project structure
- FRONTEND-AGENT: Vite + Chakra + Framer Motion, folder structure, api.ts, base components (GlassCard, GradientButton, PageWrapper, AnimatedList)
- DEVOPS-AGENT: Dockerfiles, docker-compose (+ dev), .env.example, .gitignore, CI workflow

**Validation Gate 1:** `pip install -r requirements.txt`, `alembic upgrade head`, `npm install`, `docker-compose config`

**Phase 2: Modules (backend + frontend pair per module, in parallel)**
- Auth: JWT + Google OAuth endpoints, Login/Register/Profile pages
- Roasts: GitHubService, RoastService, endpoints, Landing/History/Result/Shared pages
- Gallery + Dashboard: only if the user opts in beyond MVP

**Validation Gate 2:** `ruff check backend/`, `mypy backend/app --ignore-missing-imports`, `npm run lint`, `npm run type-check`

**Phase 3: Quality (3 agents in parallel)**
- TEST-AGENT: pytest (GitHub and LLM mocked) + RTL tests, 80%+ backend coverage
- REVIEW-AGENT: OWASP review, SSRF check on URL handling, rate limiting, prompt-injection handling (GitHub content is untrusted input to the LLM), no secrets in code
- RESEARCH-AGENT: validate FastAPI, React, Claude API, and dependency advisories

**Final Validation:** full test suite, docker build, health checks

---

## VALIDATION GATES

| Gate | Commands |
|------|----------|
| 1 | `alembic upgrade head`, `npm install`, `docker-compose config` |
| 2 | `ruff check backend/`, `mypy backend/app`, `npm run lint`, `npm run type-check` |
| 3 | `pytest backend/tests --cov=backend/app --cov-fail-under=80`, `npm test` |
| Final | `docker-compose up -d`, `curl localhost:8000/health`, `curl localhost:3000` |

---

## ENVIRONMENT VARIABLES

```env
DATABASE_URL=postgresql://user:password@localhost:5432/team14_roast
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ANTHROPIC_API_KEY=
ROAST_MODEL=claude-haiku-4-5-20251001
GITHUB_TOKEN=
VITE_API_URL=http://localhost:8000
```

Never commit real values. `.env` is gitignored; only `.env.example` is tracked.

---

## NEXT STEP

```
/execute-prp PRPs/team14-roast-prp.md
```
