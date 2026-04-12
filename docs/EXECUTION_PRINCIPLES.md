# EXECUTION_PRINCIPLES.md

# Execution Principles

> Repo-first принципы для работы с AI и orchestration. Эти правила важнее привычек чата и должны переживать смену модели.

---

## Core principles

1. **Repo over chat**  
   Контракт живет в versioned docs, tests и enforcement, а не в памяти текущей сессии.

2. **Truthfulness over speed**  
   Если capability только planned, она помечается как planned. Нельзя продавать preflight как готовый runtime.

3. **Small verifiable slices**  
   Каждый change должен иметь локальный gate, а не “кажется, это должно работать”.

4. **Reuse before reinvention**  
   Сначала использовать существующие CLI/state/auth, и только потом добавлять новые login/API flows.

5. **Explicit boundaries**  
   `/solo` и `/orch` разделены. Adapter layer и orchestration layer разделены. Human gate не растворяется в reviewer quorum.

6. **Tests before behavior expansion**  
   Новое поведение сначала описывается failing tests и только потом реализацией.

7. **Open-source honesty**  
   Репозиторий должен быть понятен внешнему читателю: что работает, что planned, где правила, где tasks, где runtime limits.

---

## Operating consequences

- docs/runtime contradiction считается дефектом
- green local gates обязательнее субъективного “выглядит нормально”
- risky runtime/auth changes требуют явного human sign-off
- low-cost parity gaps не копятся “на потом”, если их можно закрыть в пределах текущего pass
