# 🤝 Contributing to SocialSync AI

Thank you for your interest in contributing to SocialSync AI! This guide will help you get started.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Coding Standards](#coding-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Pull Request Process](#pull-request-process)
9. [Roadmap & Feature Requests](#roadmap--feature-requests)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in this project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience, education
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what is best for the community

**Unacceptable behavior:**
- ❌ Harassment, trolling, insulting comments
- ❌ Public or private harassment
- ❌ Publishing others' private information
- ❌ Conduct unbecoming of a professional

**Enforcement:**
Report violations to: [conduct@yourdomain.com](mailto:conduct@yourdomain.com)

---

## Getting Started

### Prerequisites

**Required:**
- Git
- Docker & Docker Compose
- Code editor (VS Code recommended)
- GitHub account

**Recommended:**
- Python 3.10+ (for local backend development)
- Node.js 18+ (for local frontend development)
- PostgreSQL client (for database inspection)

---

## Development Setup

### 1. Fork & Clone

```bash
# Fork repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/socialsync-ai.git
cd socialsync-ai

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/socialsync-ai.git
```

### 2. Environment Setup

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit with your API keys
# Minimum required for local dev:
# - SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
# - OPENROUTER_API_KEY or OPENAI_API_KEY
# - REDIS_URL (default: redis://redis:6379/0)
```

### 3. Start Services

```bash
# Start all services (backend, frontend, Redis, Celery workers)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access services:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Flower (Celery): http://localhost:5555
```

### 4. Run Migrations

```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
python -m app.db.migrate

# Exit container
exit
```

### 5. Verify Setup

```bash
# Test backend
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Test frontend
open http://localhost:3000
# Should show login page
```

---

## Project Structure

```
socialsync-ai/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   │   ├── rag_agent.py       # RAG Agent (LangGraph)
│   │   │   ├── automation_service.py
│   │   │   ├── comment_triage.py
│   │   │   └── escalation.py
│   │   ├── workers/           # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── comments.py    # Comment polling
│   │   │   ├── messages.py    # DM polling
│   │   │   └── scheduler.py   # Post scheduling
│   │   ├── schemas/           # Pydantic models
│   │   ├── deps/              # Dependencies
│   │   │   └── system_prompt.py
│   │   └── db/                # Database utilities
│   ├── tests/                 # Test suite
│   └── requirements.txt
├── frontend/                   # Next.js 14 frontend
│   ├── app/                   # App router
│   │   ├── (auth)/            # Auth pages
│   │   ├── dashboard/         # Protected pages
│   │   │   ├── inbox/
│   │   │   ├── comments/
│   │   │   ├── calendar/
│   │   │   └── settings/
│   │   └── api/               # API routes
│   ├── components/            # React components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── calendar/
│   │   ├── comments/
│   │   └── inbox/
│   └── lib/                   # Utilities
├── docs/                      # Documentation
│   ├── README.md
│   ├── INSTALLATION.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── features/              # Feature docs
│   └── technical/             # Technical docs
└── docker-compose.yml
```

---

## Development Workflow

### Branch Naming Convention

```bash
# Feature branches
git checkout -b feat/add-twitter-integration
git checkout -b feat/analytics-dashboard

# Bug fixes
git checkout -b fix/comment-polling-error
git checkout -b fix/escalation-email

# Documentation
git checkout -b docs/update-installation-guide

# Refactoring
git checkout -b refactor/rag-agent-tools

# Performance
git checkout -b perf/optimize-vector-search
```

### Commit Message Format

```bash
# Format: <type>(<scope>): <subject>

# Examples:
git commit -m "feat(backend): add Twitter integration"
git commit -m "fix(frontend): resolve calendar drag-and-drop bug"
git commit -m "docs(readme): update installation steps"
git commit -m "refactor(rag): extract tool creation to factory functions"
git commit -m "test(comments): add test for owner loop prevention"
git commit -m "perf(db): add index on conversation_id"

# Types:
# - feat: New feature
# - fix: Bug fix
# - docs: Documentation only
# - style: Formatting, missing semicolons (no code change)
# - refactor: Code change that neither fixes bug nor adds feature
# - perf: Performance improvement
# - test: Adding or correcting tests
# - chore: Updating build tasks, package manager configs, etc.
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

---

## Coding Standards

### Python (Backend)

**Style Guide:** PEP 8 + Black formatter

```python
# Use Black for auto-formatting
pip install black
black backend/

# Type hints required
def process_message(message_id: str, user_id: str) -> Optional[str]:
    """Process customer message with RAG agent

    Args:
        message_id: UUID of message
        user_id: UUID of user

    Returns:
        AI response text or None if error
    """
    pass

# Docstrings for all public functions
# Format: Google style docstrings
```

**Linting:**

```bash
# Install flake8
pip install flake8

# Run linter
flake8 backend/app --max-line-length=100 --exclude=migrations
```

**Import Order:**

```python
# 1. Standard library
import os
import json
from typing import List, Dict

# 2. Third-party
from fastapi import APIRouter
from langchain_core.messages import BaseMessage

# 3. Local
from app.services.rag_agent import RAGAgent
from app.schemas.messages import MessageSchema
```

### TypeScript/JavaScript (Frontend)

**Style Guide:** Airbnb + Prettier

```typescript
// Use Prettier for auto-formatting
npm install --save-dev prettier
npm run format

// Type safety required
interface Comment {
  id: string;
  text: string;
  author: string;
  createdAt: Date;
}

function renderComment(comment: Comment): JSX.Element {
  // ...
}

// Functional components + hooks preferred
export default function CommentList({ postId }: { postId: string }) {
  const [comments, setComments] = useState<Comment[]>([]);

  useEffect(() => {
    // Fetch comments
  }, [postId]);

  return <div>{/* ... */}</div>;
}
```

**ESLint:**

```bash
# Run linter
npm run lint

# Auto-fix
npm run lint --fix
```

---

## Testing Guidelines

### Backend Tests (pytest)

**Location:** `backend/tests/`

**Running Tests:**

```bash
# All tests
pytest

# Specific test file
pytest tests/test_services/test_rag_agent.py

# Specific test
pytest tests/test_services/test_rag_agent.py::test_escalation_tool

# With coverage
pytest --cov=app tests/

# Verbose output
pytest -v
```

**Writing Tests:**

```python
# tests/test_services/test_my_feature.py

import pytest
from app.services.my_service import MyService

class TestMyService:
    """Test suite for MyService

    Architecture:
    - Use fixtures for setup/teardown
    - One test per behavior
    - Clear test names (test_WHEN_THEN)
    """

    @pytest.fixture
    def service(self):
        """Create service instance"""
        return MyService(user_id="test-user-uuid")

    def test_WHEN_valid_input_THEN_returns_success(self, service):
        """Test happy path"""
        result = service.process("valid input")
        assert result.success is True

    def test_WHEN_invalid_input_THEN_raises_error(self, service):
        """Test error handling"""
        with pytest.raises(ValueError):
            service.process("")
```

**Test Coverage Target:** 80%+

**Required Tests:**
- ✅ All new features must have tests
- ✅ Bug fixes must include regression test
- ✅ Public API methods must be tested

### Frontend Tests (Jest + React Testing Library)

```bash
# Run tests
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

**Writing Tests:**

```tsx
// components/__tests__/CommentItem.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import CommentItem from '../CommentItem';

describe('CommentItem', () => {
  it('renders comment text', () => {
    render(<CommentItem text="Great post!" author="user123" />);
    expect(screen.getByText('Great post!')).toBeInTheDocument();
  });

  it('calls onReply when reply button clicked', () => {
    const handleReply = jest.fn();
    render(<CommentItem text="Hello" onReply={handleReply} />);

    fireEvent.click(screen.getByRole('button', { name: /reply/i }));
    expect(handleReply).toHaveBeenCalledTimes(1);
  });
});
```

---

## Pull Request Process

### Before Submitting

**Checklist:**

```markdown
- [ ] Tests added/updated (coverage maintained)
- [ ] Code follows style guide (Black/Prettier formatted)
- [ ] Documentation updated (if API/behavior changed)
- [ ] Commit messages follow convention
- [ ] Branch is up-to-date with main
- [ ] All tests pass locally
- [ ] No console.log/print() statements left
- [ ] No commented-out code
```

### PR Template

When creating a PR, use this template:

```markdown
## Description

Brief description of changes (1-2 sentences).

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update

## How Has This Been Tested?

Describe the tests you ran:
- Test A: ...
- Test B: ...

## Screenshots (if applicable)

[Add screenshots for UI changes]

## Checklist

- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where needed
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective
- [ ] New and existing unit tests pass locally
```

### Review Process

1. **Automated Checks** - CI runs tests, linting
2. **Maintainer Review** - 1-2 maintainers review code
3. **Feedback** - Address review comments
4. **Approval** - At least 1 approval required
5. **Merge** - Squash and merge to main

**Response Time:**
- First review: Within 3-5 days
- Follow-up reviews: Within 1-2 days

---

## Roadmap & Feature Requests

### Current Roadmap (Q1-Q3 2025)

**Q1 2025:**
- [ ] Twitter/X integration
- [ ] LinkedIn integration
- [ ] Enhanced analytics (predictive insights)
- [ ] Team collaboration (multi-user workspaces)

**Q2 2025:**
- [ ] TikTok integration
- [ ] Mobile app (React Native)
- [ ] API webhooks (custom integrations)
- [ ] Advanced scheduling (A/B testing)

**Q3 2025:**
- [ ] White-label deployment
- [ ] Custom model fine-tuning
- [ ] Voice message support
- [ ] Image generation (DALL-E, Midjourney)

### Requesting Features

**Use GitHub Discussions:**

1. Go to [Discussions](https://github.com/yvankondjo/socialsync-ai/discussions)
2. Select "Feature Request" category
3. Provide:
   - **Problem:** What problem does this solve?
   - **Solution:** How should it work?
   - **Alternatives:** What alternatives exist?
   - **Impact:** Who benefits? (businesses, creators, agencies)

**Voting:**
- 👍 Upvote features you want
- Comment with use cases
- Top-voted features prioritized

---

## Areas Needing Contributions

**High Priority:**

1. **Frontend Testing** - React component tests (coverage < 50%)
2. **API Documentation** - OpenAPI examples, error codes
3. **Mobile App** - React Native version
4. **Internationalization** - i18n support (Spanish, German, etc.)

**Medium Priority:**

5. **Platform Integrations** - Twitter, LinkedIn, TikTok
6. **Analytics Improvements** - More dashboards, export features
7. **Performance** - Optimize vector search, caching
8. **DevOps** - Kubernetes manifests, Terraform scripts

**Good First Issues:**

- 🟢 Documentation improvements
- 🟢 UI polish (spacing, colors, responsive design)
- 🟢 Error message improvements
- 🟢 Add examples to README
- 🟢 Write blog posts/tutorials

**Filter by label:** `good-first-issue`, `help-wanted`, `documentation`

---

## Getting Help

### Documentation

- **Installation:** [INSTALLATION.md](./INSTALLATION.md)
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Database:** [DATABASE.md](./DATABASE.md)
- **Features:** [features/](./features/)
- **Technical:** [technical/](./technical/)

### Community

- **GitHub Discussions** - [Ask questions](https://github.com/yvankondjo/socialsync-ai/discussions)
- **Discord** - [Join community](https://discord.gg/socialsync-ai) (Coming soon)
- **Stack Overflow** - Tag: `socialsync-ai`

### Contact Maintainers

- **Bug Reports:** [GitHub Issues](https://github.com/yvankondjo/socialsync-ai/issues)
- **Security Issues:** security@yourdomain.com (private disclosure)
- **General Questions:** [Discussions Q&A](https://github.com/yvankondjo/socialsync-ai/discussions/categories/q-a)

---

## License

By contributing, you agree that your contributions will be licensed under the **AGPL-3.0 License**.

**What this means:**
- ✅ Your code can be used commercially
- ✅ Your code can be modified
- ⚠️ Modifications must be released under AGPL-3.0
- ⚠️ Network use = distribution (must share source)

See [LICENSE](../LICENSE) for full text.

---

## Recognition

**Contributors will be:**
- ✅ Mentioned in release notes
- ✅ Featured on project website (if significant contribution)
- ✅ Recognized in GitHub contributors list

**Hall of Fame:**
- 🥇 Top contributor each quarter
- 🏆 Most impactful feature
- 📖 Best documentation improvement

---

## Thank You!

Every contribution makes SocialSync AI better for everyone. Whether you:
- 🐛 Report a bug
- 💡 Suggest a feature
- 📖 Improve documentation
- 💻 Submit code
- 🎨 Design UI improvements

**You make a difference. Thank you for being part of the community!** ❤️

---

**Last Updated:** 2025-10-30
