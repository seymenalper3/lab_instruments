# CLAUDE.md - Universal Architecture & Coding Principles

> A reusable guide for maintaining code quality and architectural consistency across all projects.
> Inspired by best practices from well-architected codebases.

---

## Quick Reference

### Project Complexity Decision Tree

```
Is this project:
├─ < 2 weeks, solo developer?
│  └─ → Use: SIMPLE architecture
│     - Single module/package
│     - Basic separation (functions/classes)
│     - Manual dependencies
│     - Standard libraries only
│
├─ 2-12 weeks, 1-3 developers?
│  └─ → Use: MEDIUM architecture
│     - Clear package structure
│     - Repository pattern
│     - Basic DI (manual or lightweight)
│     - Defined architectural pattern
│
└─ 3+ months, 3+ developers?
   └─ → Use: COMPLEX architecture
      - Multi-module (if beneficial)
      - Full DI framework
      - Clean Architecture layers
      - Comprehensive testing
```

### New Project Checklist

**Before writing code:**
- [ ] Define project scope and duration
- [ ] Choose architectural pattern (MVC/MVP/MVVM/MVI)
- [ ] Decide on layer separation strategy
- [ ] Set up folder/package structure
- [ ] Choose dependencies (prefer standard libraries)
- [ ] Set up linting/formatting tools
- [ ] Plan testing strategy

**During development:**
- [ ] Keep business logic separate from UI
- [ ] Keep data access separate from business logic
- [ ] Use interfaces for major dependencies
- [ ] Write tests for business logic
- [ ] Follow consistent naming conventions
- [ ] Refactor when you copy-paste code 3+ times

---

## Part 1: Universal Principles (ALWAYS Apply)

These principles apply to **every project**, regardless of size, platform, or team.

### 1. Separation of Concerns ⭐⭐⭐

**Principle:** Keep UI, Business Logic, and Data Access separate.

**Why:**
- Easier to test
- Easier to understand
- Easier to change
- Reduces coupling

**How to apply:**

```
Every project needs three layers:
┌─────────────────────┐
│   Presentation      │  ← UI, formatting, user interaction
├─────────────────────┤
│   Business Logic    │  ← Decisions, calculations, rules
├─────────────────────┤
│   Data Access       │  ← Database, API, file I/O
└─────────────────────┘
```

**Code Example (Generic):**

```javascript
// ❌ BAD - Everything mixed together
function onButtonClick() {
    const db = openDatabase();
    const result = db.query("SELECT * FROM users");
    const user = result[0];

    // Business logic mixed with data access
    if (user.age < 18) {
        alert("Access denied");
        return;
    }

    // UI logic mixed with everything
    document.getElementById('name').innerText = user.name;
}

// ✅ GOOD - Separated concerns
// Data Access Layer
class UserRepository {
    getUser(id) {
        const db = openDatabase();
        return db.query("SELECT * FROM users WHERE id = ?", [id]);
    }
}

// Business Logic Layer
class UserValidator {
    isAdult(user) {
        return user.age >= 18;
    }
}

// Presentation Layer
function onButtonClick() {
    const user = userRepository.getUser(currentUserId);

    if (!userValidator.isAdult(user)) {
        showError("Access denied");
        return;
    }

    displayUser(user);
}
```

### 2. Dependency Inversion ⭐⭐⭐

**Principle:** Depend on abstractions (interfaces), not concrete implementations.

**Why:**
- Makes code testable (can mock dependencies)
- Makes code flexible (can swap implementations)
- Reduces coupling

**How to apply:**

```
High-level modules should not depend on low-level modules.
Both should depend on abstractions.
```

**Code Example (Generic):**

```python
# ❌ BAD - Depends on concrete implementation
class UserService:
    def __init__(self):
        self.database = SQLiteDatabase()  # Tightly coupled!

    def get_user(self, user_id):
        return self.database.query(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ GOOD - Depends on abstraction
from abc import ABC, abstractmethod

# Abstraction (Interface)
class UserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id):
        pass

# Concrete implementation
class SQLiteUserRepository(UserRepository):
    def get_user(self, user_id):
        db = SQLiteDatabase()
        return db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Service depends on abstraction
class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_user(self, user_id):
        return self.repository.get_user(user_id)

# Can easily swap implementations or mock for testing
service = UserService(SQLiteUserRepository())
# Or for testing:
service = UserService(MockUserRepository())
```

### 3. Single Responsibility Principle ⭐⭐⭐

**Principle:** Each class/module should have ONE reason to change.

**Why:**
- Easier to understand
- Easier to test
- Easier to maintain
- More reusable

**Red Flags:**
- Class with "And" in the name: `UserManagerAndValidator`
- Class with vague names: `Helper`, `Manager`, `Util`
- Functions longer than 50 lines
- Classes with many unrelated methods

**Code Example (Generic):**

```kotlin
// ❌ BAD - Multiple responsibilities
class UserManager {
    fun validateUser(user: User): Boolean { ... }
    fun saveUser(user: User) { ... }
    fun loadUser(id: String): User { ... }
    fun sendEmail(user: User) { ... }
    fun generateReport(user: User): Report { ... }
}

// ✅ GOOD - Single responsibilities
class UserValidator {
    fun validate(user: User): Boolean { ... }
}

class UserRepository {
    fun save(user: User) { ... }
    fun load(id: String): User { ... }
}

class EmailService {
    fun sendWelcomeEmail(user: User) { ... }
}

class ReportGenerator {
    fun generateUserReport(user: User): Report { ... }
}
```

### 4. Meaningful Code Organization ⭐⭐⭐

**Principle:** Organize code by feature/domain, not by technical type.

**Why:**
- Related code stays together
- Easier to find code
- Easier to understand system
- Better encapsulation

**Code Example:**

```
❌ BAD - Organized by technical type
project/
├── controllers/
│   ├── UserController
│   ├── ProductController
│   └── OrderController
├── models/
│   ├── User
│   ├── Product
│   └── Order
├── services/
│   ├── UserService
│   ├── ProductService
│   └── OrderService
└── repositories/
    ├── UserRepository
    ├── ProductRepository
    └── OrderRepository

✅ GOOD - Organized by feature
project/
├── user/
│   ├── User (model)
│   ├── UserRepository
│   ├── UserService
│   └── UserController
├── product/
│   ├── Product (model)
│   ├── ProductRepository
│   ├── ProductService
│   └── ProductController
└── order/
    ├── Order (model)
    ├── OrderRepository
    ├── OrderService
    └── OrderController
```

### 5. Don't Repeat Yourself (DRY) ⭐⭐

**Principle:** Avoid code duplication. Extract common logic.

**Rule of Three:** If you copy-paste code 3 times, extract it.

**Code Example (Generic):**

```javascript
// ❌ BAD - Duplicated validation logic
function createUser(data) {
    if (!data.email) throw new Error("Email required");
    if (!data.email.includes('@')) throw new Error("Invalid email");
    if (!data.name) throw new Error("Name required");
    if (data.name.length < 2) throw new Error("Name too short");
    // ... create user
}

function updateUser(data) {
    if (!data.email) throw new Error("Email required");
    if (!data.email.includes('@')) throw new Error("Invalid email");
    if (!data.name) throw new Error("Name required");
    if (data.name.length < 2) throw new Error("Name too short");
    // ... update user
}

// ✅ GOOD - Extracted validation
class UserValidator {
    validate(data) {
        this.validateEmail(data.email);
        this.validateName(data.name);
    }

    validateEmail(email) {
        if (!email) throw new Error("Email required");
        if (!email.includes('@')) throw new Error("Invalid email");
    }

    validateName(name) {
        if (!name) throw new Error("Name required");
        if (name.length < 2) throw new Error("Name too short");
    }
}

function createUser(data) {
    validator.validate(data);
    // ... create user
}

function updateUser(data) {
    validator.validate(data);
    // ... update user
}
```

### 6. Consistent Naming Conventions ⭐⭐

**Principle:** Be consistent in how you name things.

**Guidelines:**
- Use descriptive names (avoid `x`, `temp`, `data`)
- Be consistent with terminology (don't mix `user` and `account`)
- Follow language conventions (camelCase in JS, snake_case in Python)
- Make booleans read like questions (`isActive`, `hasPermission`)

**Examples:**

```
✅ Good Names:
- calculateTotalPrice()
- isUserAuthenticated()
- findUserById()
- UserRepository
- activeUsers

❌ Bad Names:
- calc()
- check()
- getData()
- Manager
- temp
```

### 7. Make Business Logic Testable ⭐⭐

**Principle:** Keep business logic free from UI and infrastructure dependencies.

**Why:**
- Can test without UI framework
- Can test without database
- Faster tests
- More reliable tests

**Code Example:**

```php
// ❌ BAD - Hard to test (Laravel example)
class OrderController {
    public function checkout(Request $request) {
        $items = DB::table('cart_items')
            ->where('user_id', Auth::id())
            ->get();

        $total = 0;
        foreach ($items as $item) {
            $total += $item->price * $item->quantity;
        }

        if ($total > 1000) {
            $total *= 0.9; // 10% discount
        }

        DB::table('orders')->insert([
            'user_id' => Auth::id(),
            'total' => $total,
        ]);

        return view('checkout.success');
    }
}

// ✅ GOOD - Testable business logic
class PricingService {
    public function calculateTotal(array $items): float {
        $total = 0;
        foreach ($items as $item) {
            $total += $item['price'] * $item['quantity'];
        }
        return $total;
    }

    public function applyDiscounts(float $total): float {
        if ($total > 1000) {
            return $total * 0.9; // 10% discount
        }
        return $total;
    }
}

class OrderController {
    public function __construct(
        private CartRepository $cartRepo,
        private OrderRepository $orderRepo,
        private PricingService $pricing
    ) {}

    public function checkout(Request $request) {
        $items = $this->cartRepo->getCartItems(Auth::id());
        $total = $this->pricing->calculateTotal($items);
        $total = $this->pricing->applyDiscounts($total);

        $this->orderRepo->create(Auth::id(), $total);

        return view('checkout.success');
    }
}

// Now you can test PricingService without Laravel, DB, or Auth!
```

---

## Part 2: Context-Specific Patterns (Adapt Based on Need)

These patterns are powerful but not always necessary. Use based on project requirements.

### Multi-Module Architecture

**When to use:**
- ✅ Large projects (6+ months)
- ✅ Team of 3+ developers
- ✅ Need to share code across platforms
- ✅ Build time is slow (modules parallelize builds)

**When NOT to use:**
- ❌ Solo projects < 2 months
- ❌ Simple applications
- ❌ Prototypes/MVPs
- ❌ Still learning the basics

**Example structure:**
```
multi-module-project/
├── app/              # UI layer (depends on domain)
├── domain/           # Business logic (no dependencies)
└── data/             # Data layer (depends on domain)
```

### Dependency Injection Framework

**When to use:**
- ✅ Complex dependency graphs
- ✅ Many singleton services
- ✅ Large team (enforces consistency)
- ✅ Extensive testing

**When NOT to use:**
- ❌ Simple projects (manual DI is fine)
- ❌ < 5 classes need injection
- ❌ Prototyping

**Simple projects can use manual DI:**
```python
# Manual DI - perfectly fine for small projects
class Application:
    def __init__(self):
        self.database = Database()
        self.user_repo = UserRepository(self.database)
        self.user_service = UserService(self.user_repo)
```

### Repository Pattern

**When to use:**
- ✅ Multiple data sources (DB + API + Cache)
- ✅ Complex data access logic
- ✅ Want to abstract data layer
- ✅ Need to swap implementations

**When NOT to use:**
- ❌ Simple CRUD with single data source
- ❌ Adds unnecessary abstraction

**Generic example:**
```typescript
// Repository interface
interface UserRepository {
    findById(id: string): Promise<User>;
    save(user: User): Promise<void>;
}

// Implementation can use DB, API, or anything
class DatabaseUserRepository implements UserRepository {
    async findById(id: string): Promise<User> {
        // Database implementation
    }

    async save(user: User): Promise<void> {
        // Database implementation
    }
}
```

### Architectural Patterns

Choose based on your UI framework and team familiarity:

**MVC (Model-View-Controller)**
- **Use for:** Traditional server-rendered apps (Laravel, Rails, Django)
- **Good for:** Web backends with template engines

**MVP (Model-View-Presenter)**
- **Use for:** Traditional view-based UI (XML layouts, Qt)
- **Good for:** When you want platform-agnostic presenters

**MVVM (Model-View-ViewModel)**
- **Use for:** Reactive UI frameworks (React, Vue, Flutter, Jetpack Compose, SwiftUI)
- **Good for:** Modern UI with data binding

**MVI (Model-View-Intent)**
- **Use for:** Unidirectional data flow needs
- **Good for:** Complex state management

**For most projects:** Start with MVVM or MVC depending on framework.

### Command Pattern

**When to use:**
- ✅ Need undo/redo functionality
- ✅ Need operation history/logging
- ✅ Transactional operations
- ✅ Queue operations for later

**When NOT to use:**
- ❌ Simple CRUD operations
- ❌ No undo/redo needed
- ❌ Adds unnecessary complexity

---

## Part 3: Project Size Framework

### Small Projects (< 2 weeks, Solo)

**Architecture:**
```
src/
├── ui/              # All UI code
├── logic/           # Business logic
└── data/            # Data access
```

**Use:**
- ✅ Basic separation (3 folders/packages)
- ✅ Simple functions/classes
- ✅ Manual dependency management
- ✅ Standard libraries only
- ✅ Minimal abstraction

**Avoid:**
- ❌ Multi-module architecture
- ❌ DI frameworks
- ❌ Over-engineering
- ❌ Custom frameworks

**Example checklist:**
- [ ] Separate UI from logic
- [ ] Separate logic from data access
- [ ] Use meaningful names
- [ ] Extract duplicated code
- [ ] Write a few key tests

### Medium Projects (2-12 weeks, 1-3 developers)

**Architecture:**
```
src/
├── features/
│   ├── user/
│   │   ├── UserView
│   │   ├── UserViewModel
│   │   └── UserRepository
│   ├── product/
│   └── order/
├── shared/
│   ├── database/
│   ├── network/
│   └── utils/
└── core/
    └── models/
```

**Use:**
- ✅ Clear package/folder structure
- ✅ Repository pattern
- ✅ ViewModel/Presenter pattern
- ✅ Maybe lightweight DI
- ✅ Defined architectural pattern
- ✅ Testing strategy

**Consider:**
- ⚠️ DI framework (if getting complex)
- ⚠️ Separate modules (if growing quickly)

**Example checklist:**
- [ ] Feature-based organization
- [ ] Consistent architectural pattern
- [ ] Repository for data access
- [ ] ViewModels/Presenters for UI logic
- [ ] Interfaces for key dependencies
- [ ] Unit tests for business logic
- [ ] Code style enforcement (linter)

### Large Projects (3+ months, 3+ developers)

**Architecture:**
```
project/
├── app/              # Presentation layer
│   ├── ui/
│   ├── viewmodels/
│   └── di/
├── domain/           # Business logic (pure)
│   ├── models/
│   ├── usecases/
│   └── repositories/ # Interfaces
└── data/             # Data implementations
    ├── repositories/
    ├── database/
    └── network/
```

**Use:**
- ✅ Multi-module (if beneficial)
- ✅ Clean Architecture layers
- ✅ DI framework
- ✅ Repository pattern
- ✅ Use cases for complex logic
- ✅ Comprehensive testing
- ✅ CI/CD pipeline
- ✅ Code review process

**Consider:**
- ⚠️ Command pattern (if undo/redo)
- ⚠️ Event bus (if complex communication)
- ⚠️ Feature flags
- ⚠️ Monitoring/analytics

**Example checklist:**
- [ ] Multi-layer architecture
- [ ] Dependency injection throughout
- [ ] Repository pattern consistently applied
- [ ] Use cases for business logic
- [ ] Comprehensive test coverage
- [ ] Documentation
- [ ] CI/CD pipeline
- [ ] Code style enforcement
- [ ] Code review process
- [ ] Monitoring/error tracking

---

## Part 4: Common Anti-Patterns

### 🚫 God Class

**What:** A class that does everything.

```kotlin
// ❌ BAD
class UserManager {
    fun createUser() { }
    fun deleteUser() { }
    fun validateUser() { }
    fun sendEmail() { }
    fun generateReport() { }
    fun calculateStats() { }
    fun exportData() { }
    // 50+ more methods...
}
```

**Fix:** Split into focused classes (Single Responsibility).

### 🚫 Mixing Layers

**What:** UI code calling database directly, skipping business logic.

```javascript
// ❌ BAD
function onButtonClick() {
    const db = openDatabase();
    db.execute("UPDATE users SET balance = balance - 100");
}
```

**Fix:** Always go through proper layers (UI → Logic → Data).

### 🚫 Hardcoded Dependencies

**What:** Creating dependencies with `new` instead of injecting.

```python
# ❌ BAD
class UserService:
    def __init__(self):
        self.repo = UserRepository()  # Hardcoded!
        self.validator = UserValidator()  # Hardcoded!
```

**Fix:** Inject dependencies through constructor.

### 🚫 Primitive Obsession

**What:** Using primitive types instead of domain objects.

```java
// ❌ BAD
public void processPayment(String userId, double amount, String currency) { }

// ✅ GOOD
public void processPayment(UserId userId, Money amount) { }
```

### 🚫 Comments Explaining Bad Code

**What:** Using comments to explain confusing code instead of rewriting it.

```javascript
// ❌ BAD
// Get the user's total purchase amount and apply discount if over 1000
let t = 0;
for (let i of d) {
    t += i.p * i.q;
}
if (t > 1000) t *= 0.9;

// ✅ GOOD (self-documenting)
const total = calculateTotal(items);
const finalTotal = applyDiscounts(total);
```

### 🚫 Utility Classes

**What:** Classes with only static methods (often named `Helper` or `Util`).

```csharp
// ❌ BAD (often hides poor design)
public static class StringHelper {
    public static string FormatName(string name) { }
    public static string Capitalize(string text) { }
}
```

**Consider:** Should this be an instance method? Extension method? Is there a better place?

---

## Part 5: Claude Code Integration

### How to Use This File

1. **Copy to each new project:**
   ```bash
   cp ~/CLAUDE.md ./CLAUDE.md
   ```

2. **Reference in prompts:**
   ```
   "Create a new user authentication feature following the principles in CLAUDE.md"
   ```

3. **Ask for architecture review:**
   ```
   "Review my code against CLAUDE.md and suggest improvements"
   ```

4. **Request pattern application:**
   ```
   "Refactor this code to follow the separation of concerns principle from CLAUDE.md"
   ```

### Example Prompts for Claude

**Starting a new project:**
```
I'm starting a [Android/Web/Python] project that will take approximately [duration] with a team of [size].

Based on CLAUDE.md, help me:
1. Choose the appropriate architecture
2. Set up the initial project structure
3. Define the layers and their responsibilities
```

**During development:**
```
I'm implementing [feature]. According to CLAUDE.md principles, help me:
1. Organize this code properly
2. Separate concerns correctly
3. Apply the right patterns for this use case
```

**Code review:**
```
Review this code against CLAUDE.md principles and check for:
1. Separation of concerns
2. Dependency inversion
3. Single responsibility
4. Anti-patterns
```

**Refactoring:**
```
This code violates [principle] from CLAUDE.md. Help me refactor it to:
1. Follow the principle correctly
2. Maintain the same functionality
3. Add appropriate tests
```

### Project-Specific Adaptations

Create `.claude/project-context.md` in each project:

```markdown
# Project-Specific Context

## Project Type
[Android/Web/Backend/etc.]

## Architecture Chosen
[MVC/MVVM/Clean Architecture/etc.]

## Layer Structure
- Presentation: [description]
- Business Logic: [description]
- Data: [description]

## Patterns in Use
- [ ] Repository Pattern
- [ ] Dependency Injection: [framework or manual]
- [ ] [Other patterns]

## Naming Conventions
- ViewModels: `*ViewModel`
- Repositories: `*Repository`
- [etc.]

## Testing Strategy
- Unit tests for: [what]
- Integration tests for: [what]
- [etc.]
```

---

## Part 6: Decision Framework

When making architectural decisions, ask:

### Question 1: Project Complexity
```
How long will this project take?
├─ < 2 weeks → Simple architecture
├─ 2-12 weeks → Medium architecture
└─ 3+ months → Complex architecture (consider Clean Arch)
```

### Question 2: Team Size
```
How many developers?
├─ Solo → Minimize overhead, focus on clarity
├─ 2-3 → Consistent patterns, basic structure
└─ 3+ → Full architecture, enforce standards
```

### Question 3: Pattern Justification
```
Before adding a pattern, ask:
1. Does this solve a real problem we have NOW?
2. Will this make the code easier to understand?
3. Will this make the code easier to test?
4. Is the benefit worth the added complexity?

If "No" to most → Don't add it yet (YAGNI principle)
```

### Question 4: Abstraction Level
```
How much abstraction do I need?
├─ Can I do this with simple functions? → Do that
├─ Do I need classes? → Use classes
├─ Do I need interfaces? → Only if swapping implementations
└─ Do I need multiple modules? → Only if clear benefit
```

---

## Summary: Core Takeaways

### Always Apply (Every Project)
1. ✅ Separation of Concerns (UI/Logic/Data)
2. ✅ Dependency Inversion (depend on interfaces)
3. ✅ Single Responsibility (one class, one job)
4. ✅ Meaningful Organization (feature-based)
5. ✅ DRY Principle (extract duplicates)
6. ✅ Consistent Naming
7. ✅ Testable Business Logic

### Apply Based on Context
1. ⚙️ Multi-module → Only if project is large
2. ⚙️ DI Framework → Manual DI fine for small projects
3. ⚙️ Repository Pattern → Only if multiple data sources
4. ⚙️ Complex Patterns → Only when they solve real problems

### Remember
- **Start simple, add complexity only when needed**
- **Patterns should serve your code, not vice versa**
- **The best architecture is the simplest one that works**
- **Refactor when you feel pain, not preemptively**

---

## Version
- **Created:** [Date]
- **For projects:** Cross-platform (Android, Web, Backend, Python GUI)
- **Last updated:** [Date]

---

**Next Steps:**
1. Copy this file to your new project
2. Read the Quick Reference for your project size
3. Apply Universal Principles from Part 1
4. Choose patterns from Part 2 based on need
5. Reference this file when working with Claude Code
