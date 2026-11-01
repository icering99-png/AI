// devops_quest/js/workflow_simulator.js — Симуляторы PR, Merge-конфликтов и CI/CD пайплайна

class WorkflowSimulator {
  constructor() {
    this.resetState();
  }

  resetState() {
    this.prState = {
      id: 12,
      title: "Интеграция базы знаний тарифов для бота МТС",
      author: "danil",
      sourceBranch: "danil/tariffs",
      targetBranch: "main",
      status: "OPEN", // OPEN, MERGED, CONFLICT
      approvedByAndrey: false,
      diff: [
        { type: "header", text: "diff --git a/answers.py b/answers.py" },
        { type: "info", text: "@@ -1,4 +1,8 @@" },
        { type: "del", text: '-greeting = "Здравствуйте!"' },
        { type: "add", text: '+greeting = "Здравствуйте! Чем я могу вам помочь?"' },
        { type: "add", text: '+def get_tariffs():' },
        { type: "add", text: '+    return "Базовый тариф от 150 тыс руб."' }
      ],
      comments: [
        {
          author: "Андрей (Lead Architect)",
          text: "Данил, код выглядит чисто! Но обязательно запусти CI пайплайн и убедись, что нет конфликтов с main перед слиянием."
        }
      ]
    };

    this.hasConflict = false;
    this.conflictResolved = false;

    this.cicdState = {
      running: false,
      hasError: false,
      fixedError: false,
      stages: {
        lint: "pending",
        unit: "pending",
        e2e: "pending",
        deploy: "pending"
      },
      logs: []
    };
  }

  // --- PR & Conflict Logic ---

  triggerConflict() {
    this.hasConflict = true;
    this.conflictResolved = false;
    this.prState.status = "CONFLICT";
    this.prState.comments.push({
      author: "GitHub Bot",
      text: "⚠️ Слияние заблокировано: обнаружен автоматический конфликт в answers.py. Разрешите его в веб-редакторе."
    });
    return {
      incoming: 'greeting = "Добрый день! Я помощник МТС."',
      current: 'greeting = "Здравствуйте! Чем я могу вам помочь?"'
    };
  }

  resolveConflict(choice) {
    this.hasConflict = false;
    this.conflictResolved = true;
    this.prState.status = "OPEN";
    this.prState.approvedByAndrey = true;

    let chosenText = "";
    if (choice === "incoming") chosenText = 'greeting = "Добрый день! Я помощник МТС."';
    else if (choice === "current") chosenText = 'greeting = "Здравствуйте! Чем я могу вам помочь?"';
    else chosenText = 'greeting = "Добрый день! Я помощник МТС. Чем могу помочь?"';

    this.prState.diff = [
      { type: "header", text: "diff --git a/answers.py b/answers.py (КОНФЛИКТ РАЗРЕШЕН)" },
      { type: "info", text: "@@ Слияние успешно зафиксировано @@" },
      { type: "add", text: `+${chosenText}` }
    ];

    this.prState.comments.push({
      author: "Андрей (Lead Architect)",
      text: "Отлично, конфликт разрешен корректно! Я проверил diff и одобряю слияние (Approve). Нажимай Merge!"
    });

    return { success: true, chosenText };
  }

  abortConflict() {
    this.hasConflict = false;
    this.prState.status = "OPEN";
    return { success: true, msg: "Слияние отменено командой 'git merge --abort'. Репозиторий возвращен в исходное состояние." };
  }

  mergePR() {
    if (this.hasConflict) {
      return { success: false, msg: "Нельзя выполнить Merge: сначала разрешите конфликт слияния!" };
    }
    if (!this.prState.approvedByAndrey) {
      return { success: false, msg: "Ветка защищена: требуется одобрение (Approve) от Андрея!" };
    }
    this.prState.status = "MERGED";
    return { success: true, msg: "УСПЕХ! Ветка danil/tariffs влита в main (Merge commit: a8f912e). Ветка на сервере удалена." };
  }

  // --- CI/CD Logic ---

  setBreakPipeline(shouldBreak) {
    this.cicdState.hasError = shouldBreak;
    this.cicdState.fixedError = !shouldBreak;
  }

  async runPipeline(onProgressUpdate) {
    this.cicdState.running = true;
    this.cicdState.logs = [];

    const appendLog = (line) => {
      this.cicdState.logs.push(`[${new Date().toLocaleTimeString()}] ${line}`);
      if (onProgressUpdate) onProgressUpdate(this.cicdState);
    };

    appendLog("🚀 Запуск Runner (ubuntu-latest): GitHub Actions v4...");
    appendLog("📥 actions/checkout@v4: Клонирование репозитория danil/tariffs...");
    appendLog("🐍 actions/setup-python@v5: Подключение Python 3.11.8...");

    // Stage 1: Lint
    this.cicdState.stages.lint = "running";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);
    await this.delay(700);

    appendLog("🔍 [Stage 1] Запуск flake8 & ruff: проверка стиля и PEP8...");
    appendLog("✓ flake8: 0 ошибок, стиль кода безупречен.");
    this.cicdState.stages.lint = "passed";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);

    // Stage 2: Unit tests
    this.cicdState.stages.unit = "running";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);
    await this.delay(900);

    appendLog("🧪 [Stage 2] Запуск Pytest: pytest tests/ -v...");

    if (this.cicdState.hasError && !this.cicdState.fixedError) {
      appendLog("FAIL: tests/test_masking.py::test_mask_personal_data");
      appendLog("AssertionError: Не маскирован номер телефона '+7 999 123-45-67'! Нарушение политики ИБ МТС.");
      appendLog("❌ PIPELINE FAILED: 1 failed, 12 passed in 1.42s");
      this.cicdState.stages.unit = "failed";
      this.cicdState.stages.e2e = "pending";
      this.cicdState.stages.deploy = "pending";
      this.cicdState.running = false;
      if (onProgressUpdate) onProgressUpdate(this.cicdState);
      return { success: false, stage: "unit" };
    }

    appendLog("✓ tests/test_masking.py: 5/5 passed (Маскировка ПДн подтверждена)");
    appendLog("✓ tests/test_tariffs.py: 8/8 passed (Ответы по базе знаний подтверждены)");
    this.cicdState.stages.unit = "passed";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);

    // Stage 3: Playwright E2E
    this.cicdState.stages.e2e = "running";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);
    await this.delay(1000);

    appendLog("🎭 [Stage 3] Запуск Playwright: npx playwright test (Chromium Headless)...");
    appendLog("✓ e2e/chat_flow.spec.ts: Открытие виджета чата -> ввод вопроса -> ответ получен за 1.8s");
    this.cicdState.stages.e2e = "passed";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);

    // Stage 4: Deploy
    this.cicdState.stages.deploy = "running";
    if (onProgressUpdate) onProgressUpdate(this.cicdState);
    await this.delay(800);

    appendLog("🚀 [Stage 4] Развертывание в Staging (mts-staging.internal)...");
    appendLog("✓ Docker container deployed. Health check: 200 OK.");
    this.cicdState.stages.deploy = "passed";
    this.cicdState.running = false;

    if (onProgressUpdate) onProgressUpdate(this.cicdState);
    return { success: true };
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { WorkflowSimulator };
}
