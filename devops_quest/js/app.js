// devops_quest/js/app.js — Главный контроллер приложения DevOps Quest

document.addEventListener("DOMContentLoaded", () => {
  // 1. Инициализация подсистем
  const gitSim = new GitSimulator();
  const workSim = new WorkflowSimulator();

  // Состояние пользователя
  const STORAGE_KEY = "devops_quest_user_profile_v1";
  let userProfile = loadUserProfile();
  touchDailyStreak();
  renderDailyRitual();

  let activeLesson = null;
  let examQuestions = [];
  let currentExamIndex = 0;
  let activeExamMode = "emergency";

  // 2. Навигация по вкладкам
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      tabButtons.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById(targetId).classList.add("active");

      if (targetId === "tab-terminal") {
        updateTerminalUI();
      } else if (targetId === "tab-pr") {
        updatePrUI();
      }
    });
  });

  // 3. Рендеринг учебной программы
  renderCurriculum();
  renderCheatsheet();
  updateUserStatsUI();

  // --- Curriculum logic ---
  function renderCurriculum() {
    const listEl = document.getElementById("module-list");
    if (!listEl || typeof DEVOPS_CURRICULUM === "undefined") return;

    listEl.innerHTML = "";
    DEVOPS_CURRICULUM.forEach(mod => {
      const groupEl = document.createElement("div");
      groupEl.className = "module-group";

      const titleEl = document.createElement("div");
      titleEl.className = "module-title";
      titleEl.textContent = mod.title;
      groupEl.appendChild(titleEl);

      mod.lessons.forEach(les => {
        const itemEl = document.createElement("div");
        itemEl.className = "lesson-item";
        itemEl.setAttribute("data-id", les.id);
        if (userProfile.completedLessons.includes(les.id)) {
          itemEl.classList.add("completed");
        }
        itemEl.textContent = les.title;

        itemEl.addEventListener("click", () => {
          document.querySelectorAll(".lesson-item").forEach(i => i.classList.remove("active"));
          itemEl.classList.add("active");
          showLesson(mod, les);
        });

        groupEl.appendChild(itemEl);
      });

      listEl.appendChild(groupEl);
    });

    // Автовыбор первого урока
    if (DEVOPS_CURRICULUM.length > 0 && DEVOPS_CURRICULUM[0].lessons.length > 0) {
      showLesson(DEVOPS_CURRICULUM[0], DEVOPS_CURRICULUM[0].lessons[0]);
      const firstItem = listEl.querySelector(".lesson-item");
      if (firstItem) firstItem.classList.add("active");
    }
  }

  function showLesson(mod, les) {
    activeLesson = les;
    const breadcrumbsEl = document.getElementById("lesson-breadcrumbs");
    const contentEl = document.getElementById("lesson-content");

    if (breadcrumbsEl) breadcrumbsEl.textContent = `${mod.title} > ${les.title}`;
    if (contentEl) {
      contentEl.innerHTML = renderMarkdown(les.content);
    }

    // Отмечаем прогресс
    if (!userProfile.completedLessons.includes(les.id)) {
      userProfile.completedLessons.push(les.id);
      addXP(15);
      saveUserProfile();
      updateUserStatsUI();
      const el = document.querySelector(`.lesson-item[data-id="${les.id}"]`);
      if (el) el.classList.add("completed");
    }
  }

  // Простой markdown-рендерер
  function renderMarkdown(md) {
    if (!md) return "";
    let html = md.trim();

    // Заголовки
    html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
    html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
    html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

    // Блоки кода
    html = html.replace(/```([a-z0-9]*)\n([\s\S]*?)```/gim, (match, lang, code) => {
      const esc = code.replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return `<pre><code class="lang-${lang}">${esc}</code></pre>`;
    });

    // Инлайн код
    html = html.replace(/`([^`]+)`/gim, "<code>$1</code>");

    // Списки
    html = html.replace(/^\* (.*$)/gim, "<li>$1</li>");
    html = html.replace(/((?:<li>.*<\/li>\s*)+)/gim, "<ul>$1</ul>");

    // Жирный текст
    html = html.replace(/\*\*([^*]+)\*\*/gim, "<strong>$1</strong>");

    // Абзацы
    html = html.split("\n\n").map(block => {
      if (block.startsWith("<h") || block.startsWith("<ul") || block.startsWith("<div") || block.startsWith("<pre")) {
        return block;
      }
      return `<p>${block.replace(/\n/g, "<br>")}</p>`;
    }).join("");

    return html;
  }

  // Кнопка следующего урока
  document.getElementById("btn-next-lesson")?.addEventListener("click", () => {
    goToNextLesson();
  });

  function goToNextLesson() {
    if (!activeLesson) return;
    let foundCurrent = false;
    let nextLes = null;
    let nextMod = null;

    for (const mod of DEVOPS_CURRICULUM) {
      for (const les of mod.lessons) {
        if (foundCurrent) {
          nextLes = les;
          nextMod = mod;
          break;
        }
        if (les.id === activeLesson.id) {
          foundCurrent = true;
        }
      }
      if (nextLes) break;
    }

    if (nextLes && nextMod) {
      document.querySelectorAll(".lesson-item").forEach(i => i.classList.remove("active"));
      const targetItem = document.querySelector(`.lesson-item[data-id="${nextLes.id}"]`);
      if (targetItem) {
        targetItem.classList.add("active");
        targetItem.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
      showLesson(nextMod, nextLes);
    } else {
      alert("🎉 Поздравляем! Вы прошли все доступные уроки курса! Теперь переходите во вкладку 'Экзамен / Собеседование' для финального закрепления.");
    }
  }

  // Кнопка быстрой проверки знаний в уроке
  document.getElementById("btn-solve-quiz")?.addEventListener("click", () => {
    if (!activeLesson) return;
    // 1. Ищем вопросы, точно привязанные к текущему уроку:
    let candidates = DEVOPS_QUESTIONS.filter(q => q.lessonId === activeLesson.id);
    
    // 2. Если нет точного совпадения по уроку, ищем по модулю:
    if (candidates.length === 0) {
      const modPrefix = activeLesson.id.split("-").slice(0, 2).join("-");
      candidates = DEVOPS_QUESTIONS.filter(q => q.moduleId === modPrefix);
    }

    const selectedQ = candidates.length > 0 
      ? candidates[Math.floor(Math.random() * candidates.length)]
      : DEVOPS_QUESTIONS[Math.floor(Math.random() * DEVOPS_QUESTIONS.length)];

    openModalQuiz(prepareRandomizedQuestion(selectedQ));
  });

  // Поиск по модулям
  document.getElementById("module-search")?.addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase().trim();
    document.querySelectorAll(".lesson-item").forEach(item => {
      const match = item.textContent.toLowerCase().includes(val);
      item.style.display = match ? "flex" : "none";
    });
  });

  // --- 4. Git Terminal Logic ---
  const termInput = document.getElementById("term-input");
  const termOutput = document.getElementById("terminal-output");

  termInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const cmd = termInput.value;
      termInput.value = "";
      handleTerminalCommand(cmd);
    }
  });

  document.querySelectorAll(".cmd-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const cmd = chip.getAttribute("data-cmd");
      if (cmd) {
        handleTerminalCommand(cmd);
      }
    });
  });

  document.getElementById("btn-clear-term")?.addEventListener("click", () => {
    if (termOutput) termOutput.innerHTML = "";
  });

  document.getElementById("btn-reset-repo")?.addEventListener("click", () => {
    gitSim.resetState();
    updateTerminalUI();
    appendTermLine("Репозиторий сброшен к начальному состоянию.", "warning");
  });

  function handleTerminalCommand(cmd) {
    if (!cmd.trim()) return;
    appendTermLine(`$ ${cmd}`, "cmd");

    const res = gitSim.execute(cmd);
    appendTermLine(res.out, res.type);

    if (res.type === "success") {
      addXP(10);
      userProfile.competencies.git = Math.min(100, userProfile.competencies.git + 3);
      saveUserProfile();
      updateUserStatsUI();
    } else if (res.type === "error" && res.out.includes("СТОРОЖ АНДРЕЯ")) {
      userProfile.competencies.sec = Math.min(100, userProfile.competencies.sec + 5);
      saveUserProfile();
      updateUserStatsUI();
    }

    updateTerminalUI();
  }

  function appendTermLine(text, type) {
    if (!termOutput) return;
    const line = document.createElement("div");
    line.className = `term-line ${type}`;
    line.textContent = text;
    termOutput.appendChild(line);
    termOutput.scrollTop = termOutput.scrollHeight;
  }

  function updateTerminalUI() {
    // Ветка в шапке
    const branchLabel = document.getElementById("current-branch-label");
    if (branchLabel) branchLabel.textContent = gitSim.currentBranch;

    // Списки файлов
    const wtEl = document.getElementById("working-tree-files");
    const stEl = document.getElementById("staged-files");

    if (wtEl) {
      wtEl.innerHTML = gitSim.workingTree.length === 0 ? "<li>(пусто)</li>" :
        gitSim.workingTree.map(f => `<li class="${f.status}">[${f.status}] ${f.name}</li>`).join("");
    }
    if (stEl) {
      stEl.innerHTML = gitSim.stagingArea.length === 0 ? "<li>(пусто)</li>" :
        gitSim.stagingArea.map(f => `<li class="staged">[staged] ${f.name}</li>`).join("");
    }

    // Визуализация графа коммитов
    const graphEl = document.getElementById("git-graph-canvas");
    if (graphEl) {
      graphEl.innerHTML = "";
      const currentList = gitSim.branches[gitSim.currentBranch] || [];
      const reversed = [...currentList].reverse();

      reversed.forEach((cid, idx) => {
        const c = gitSim.commits[cid];
        const isHead = cid === gitSim.head;
        const row = document.createElement("div");
        row.className = "graph-commit";
        row.innerHTML = `
          <span>●</span>
          <span class="commit-hash">${c.hash}</span>
          ${isHead ? `<span class="commit-branch-tag">HEAD -> ${gitSim.currentBranch}</span>` : ""}
          <span class="commit-msg">${c.msg} (${c.author})</span>
        `;
        graphEl.appendChild(row);
      });
    }

    // Лента Сторожа Андрея
    const safetyEl = document.getElementById("safety-log");
    if (safetyEl) {
      if (gitSim.safetyAlerts.length === 0) {
        safetyEl.innerHTML = '<div class="safety-item clean">Нарушений нет. Правила Андрея соблюдаются.</div>';
      } else {
        safetyEl.innerHTML = gitSim.safetyAlerts.map(a => `<div class="safety-item blocked">${a.replace(/\n/g, "<br>")}</div>`).join("");
      }
    }
  }

  // --- 5. PR & Workflow Logic ---
  function updatePrUI() {
    const diffContainer = document.getElementById("diff-file-container");
    if (diffContainer) {
      diffContainer.innerHTML = workSim.prState.diff.map(line => {
        let cls = "diff-line";
        if (line.type === "add") cls += " add";
        if (line.type === "del") cls += " del";
        return `<div class="${cls}">${line.text.replace(/</g, "&lt;")}</div>`;
      }).join("");
    }

    const commentsList = document.getElementById("review-comments");
    if (commentsList) {
      commentsList.innerHTML = workSim.prState.comments.map(c => `
        <div class="comment-box">
          <div class="comment-author">${c.author}</div>
          <div class="comment-text">${c.text}</div>
        </div>
      `).join("");
    }

    const mergeBtn = document.getElementById("btn-merge-pr");
    if (mergeBtn) {
      mergeBtn.disabled = !workSim.prState.approvedByAndrey || workSim.hasConflict || workSim.prState.status === "MERGED";
    }

    const statusBadge = document.getElementById("pr-status-badge");
    if (statusBadge) {
      if (workSim.prState.status === "MERGED") {
        statusBadge.className = "badge pr-open";
        statusBadge.textContent = "Merged в main ✓";
      } else if (workSim.hasConflict) {
        statusBadge.className = "badge badge-warning";
        statusBadge.textContent = "Конфликт слияния!";
      } else if (workSim.prState.approvedByAndrey) {
        statusBadge.className = "badge pr-open";
        statusBadge.textContent = "Одобрено Андреем (Approved)";
      } else {
        statusBadge.className = "badge badge-warning";
        statusBadge.textContent = "Требуется ревью Андрея";
      }
    }
  }

  document.getElementById("btn-trigger-conflict")?.addEventListener("click", () => {
    workSim.triggerConflict();
    document.getElementById("conflict-resolver-card")?.classList.remove("hidden");
    updatePrUI();
  });

  document.getElementById("btn-accept-incoming")?.addEventListener("click", () => {
    workSim.resolveConflict("incoming");
    document.getElementById("conflict-resolver-card")?.classList.add("hidden");
    addXP(40);
    userProfile.competencies.pr = Math.min(100, userProfile.competencies.pr + 10);
    saveUserProfile();
    updateUserStatsUI();
    updatePrUI();
    alert("Конфликт разрешен в пользу версии Андрея (Incoming).");
  });

  document.getElementById("btn-accept-current")?.addEventListener("click", () => {
    workSim.resolveConflict("current");
    document.getElementById("conflict-resolver-card")?.classList.add("hidden");
    addXP(40);
    userProfile.competencies.pr = Math.min(100, userProfile.competencies.pr + 10);
    saveUserProfile();
    updateUserStatsUI();
    updatePrUI();
    alert("Конфликт разрешен в пользу вашей версии (Current).");
  });

  document.getElementById("btn-accept-both")?.addEventListener("click", () => {
    workSim.resolveConflict("both");
    document.getElementById("conflict-resolver-card")?.classList.add("hidden");
    addXP(50);
    userProfile.competencies.pr = Math.min(100, userProfile.competencies.pr + 12);
    saveUserProfile();
    updateUserStatsUI();
    updatePrUI();
    alert("Оба варианта объединены. Конфликт успешно устранен!");
  });

  document.getElementById("btn-abort-conflict")?.addEventListener("click", () => {
    const res = workSim.abortConflict();
    document.getElementById("conflict-resolver-card")?.classList.add("hidden");
    updatePrUI();
    alert(res.msg);
  });

  document.getElementById("btn-merge-pr")?.addEventListener("click", () => {
    const res = workSim.mergePR();
    if (res.success) {
      addXP(100);
      userProfile.competencies.pr = Math.min(100, userProfile.competencies.pr + 15);
      saveUserProfile();
      updateUserStatsUI();
      updatePrUI();
      alert(res.msg);
    } else {
      alert(res.msg);
    }
  });

  // --- 6. CI/CD Logic ---
  document.getElementById("btn-run-pipeline")?.addEventListener("click", () => {
    runCicdPipeline();
  });

  document.getElementById("btn-break-pipeline")?.addEventListener("click", () => {
    workSim.setBreakPipeline(true);
    runCicdPipeline();
  });

  document.getElementById("btn-fix-yaml")?.addEventListener("click", () => {
    workSim.setBreakPipeline(false);
    alert("Ошибка исправлена: шлюз маскировки ПДн восстановлен! Запускаем чистый Pipeline.");
    runCicdPipeline();
  });

  function runCicdPipeline() {
    const logBox = document.getElementById("cicd-log-output");
    const stageMap = {
      lint: document.getElementById("stage-lint"),
      unit: document.getElementById("stage-unit"),
      e2e: document.getElementById("stage-e2e"),
      deploy: document.getElementById("stage-deploy")
    };

    const oldBanner = document.getElementById("cicd-next-step-banner");
    if (oldBanner) oldBanner.remove();

    workSim.runPipeline((state) => {
      // Обновление логов
      if (logBox) {
        logBox.textContent = state.logs.join("\n");
        logBox.scrollTop = logBox.scrollHeight;
      }

      // Обновление статусов стадий
      for (const [key, status] of Object.entries(state.stages)) {
        const el = stageMap[key];
        if (el) {
          const statusText = el.querySelector(".step-status");
          if (statusText) {
            statusText.className = `step-status status-${status}`;
            if (status === "running") statusText.textContent = "Выполняется...";
            else if (status === "passed") statusText.textContent = "Успешно ✓";
            else if (status === "failed") statusText.textContent = "ОШИБКА ❌";
            else statusText.textContent = "Ожидание";
          }
        }
      }
    }).then(res => {
      if (res.success) {
        addXP(60);
        userProfile.competencies.cicd = Math.min(100, userProfile.competencies.cicd + 10);
        userProfile.competencies.qa = Math.min(100, userProfile.competencies.qa + 10);
        saveUserProfile();
        updateUserStatsUI();

        // Показываем четкий следующий шаг
        const banner = document.createElement("div");
        banner.id = "cicd-next-step-banner";
        banner.className = "callout";
        banner.style.marginTop = "14px";
        banner.innerHTML = `
          <h4 style="color: var(--accent-green); margin-bottom: 6px;">🎉 ПРОВЕРКА ЗАВЕРШЕНА: ВСЕ 4 ЭТАПА ПРОЙДЕНЫ УСПЕШНО!</h4>
          <p>Все тесты (Lint, Pytest, Playwright E2E) зеленые. Сервер в Staging успешно развернут.</p>
          <div style="margin-top: 10px;">
            <button id="btn-goto-pr" class="btn btn-primary">Перейти к Pull Request и слить в main →</button>
          </div>
        `;
        document.querySelector(".pipeline-console")?.appendChild(banner);
        document.getElementById("btn-goto-pr")?.addEventListener("click", () => {
          document.querySelector('.tab-btn[data-tab="tab-pr"]')?.click();
        });
      }
    });
  }

  // --- Вспомогательные алгоритмы рандомизации вопросов и ответов ---
  function shuffleArray(array) {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  function prepareRandomizedQuestion(q) {
    if (!q || !q.options) return q;
    const indexedOptions = q.options.map((opt, idx) => ({ text: opt, isCorrect: idx === q.correctIndex }));
    const shuffledOptions = shuffleArray(indexedOptions);
    const newCorrectIndex = shuffledOptions.findIndex(o => o.isCorrect);
    return {
      ...q,
      options: shuffledOptions.map(o => o.text),
      correctIndex: newCorrectIndex
    };
  }

  // --- 7. Exam & Interview Logic ---
  document.getElementById("btn-start-exam")?.addEventListener("click", () => {
    const mode = document.querySelector('input[name="exam-mode"]:checked')?.value || "emergency";
    activeExamMode = mode;
    startExam(mode);
  });

  function startExam(mode) {
    currentExamIndex = 0;
    const allShuffled = shuffleArray(DEVOPS_QUESTIONS);

    if (mode === "emergency") {
      // Интенсив: отбираем 15 случайных сбалансированных вопросов из разных категорий
      const categoryBuckets = {};
      allShuffled.forEach(q => {
        const cat = q.category || "devops";
        if (!categoryBuckets[cat]) categoryBuckets[cat] = [];
        categoryBuckets[cat].push(q);
      });

      const selectedQuestions = [];
      const categories = Object.keys(categoryBuckets);
      let catIdx = 0;
      while (selectedQuestions.length < 15 && selectedQuestions.length < allShuffled.length) {
        const cat = categories[catIdx % categories.length];
        if (categoryBuckets[cat] && categoryBuckets[cat].length > 0) {
          selectedQuestions.push(categoryBuckets[cat].pop());
        }
        catIdx++;
      }
      
      // Если еще не набрали 15, добираем из оставшихся вопросов
      if (selectedQuestions.length < 15) {
        const remaining = allShuffled.filter(q => !selectedQuestions.some(sq => sq.id === q.id));
        selectedQuestions.push(...remaining.slice(0, 15 - selectedQuestions.length));
      }

      examQuestions = shuffleArray(selectedQuestions).map(prepareRandomizedQuestion);
    } else {
      // Полный экзамен / собеседование: все 42+ вопроса в случайном порядке со случайным порядком вариантов
      examQuestions = allShuffled.map(prepareRandomizedQuestion);
    }
    renderCurrentExamQuestion();
  }

  function renderCurrentExamQuestion() {
    const container = document.getElementById("exam-card-container");
    if (!container) return;

    if (currentExamIndex >= examQuestions.length) {
      container.innerHTML = `
        <div class="quiz-box">
          <h2>🎉 Экзамен завершен!</h2>
          <p>Вы успешно ответили на все вопросы режима. Ваши компетенции обновлены.</p>
          <button id="btn-restart-exam" class="btn btn-primary">Пройти еще раз</button>
        </div>
      `;
      document.getElementById("btn-restart-exam")?.addEventListener("click", () => startExam(activeExamMode));
      return;
    }

    const q = examQuestions[currentExamIndex];
    container.innerHTML = `
      <div class="quiz-box">
        <div class="question-header">
          <div class="question-meta">
            <span class="badge badge-warning">Вопрос ${currentExamIndex + 1} из ${examQuestions.length}</span>
            <span class="badge">${q.level}</span>
            <span class="badge">${q.category.toUpperCase()}</span>
          </div>
          <h3 class="question-title">${q.title}</h3>
          <p style="margin-top: 8px;">${q.question}</p>
        </div>

        <div class="options-list">
          ${q.options.map((opt, idx) => `
            <button class="option-btn" data-idx="${idx}">${opt}</button>
          `).join("")}
        </div>

        <div id="exam-explanation-area" class="explanation-area"></div>
      </div>
    `;

    container.querySelectorAll(".option-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const selectedIdx = parseInt(btn.getAttribute("data-idx"));
        evaluateExamAnswer(q, selectedIdx, container);
      });
    });
  }

  function evaluateExamAnswer(q, chosenIdx, container) {
    const buttons = container.querySelectorAll(".option-btn");
    buttons.forEach(b => b.disabled = true);

    const isCorrect = chosenIdx === q.correctIndex;
    const chosenBtn = buttons[chosenIdx];
    const correctBtn = buttons[q.correctIndex];

    if (isCorrect) {
      chosenBtn.classList.add("correct");
      addXP(30);
      userProfile.answeredQuestions.push(q.id);
      if (q.category in userProfile.competencies) {
        userProfile.competencies[q.category] = Math.min(100, userProfile.competencies[q.category] + 5);
      }
    } else {
      chosenBtn.classList.add("wrong");
      correctBtn.classList.add("correct");
      addXP(-5);
    }
    saveUserProfile();
    updateUserStatsUI();

    const explArea = container.querySelector("#exam-explanation-area");
    if (explArea) {
      explArea.innerHTML = `
        <div class="explanation-card ${isCorrect ? "success" : "failure"}">
          <h4>${isCorrect ? "✓ ВЕРНО!" : "❌ ОШИБКА!"}</h4>
          <p style="margin: 6px 0;"><strong>Разбор:</strong> ${q.explanation}</p>
          <p style="margin-top: 6px; color: var(--accent-yellow);"><strong>💡 Заметка для собеседования:</strong> ${q.interviewNote}</p>
          <div style="margin-top: 14px;">
            <button id="btn-next-question" class="btn btn-primary">Следующий вопрос (${currentExamIndex + 1}/${examQuestions.length}) →</button>
          </div>
        </div>
      `;
      document.getElementById("btn-next-question")?.addEventListener("click", () => {
        currentExamIndex++;
        renderCurrentExamQuestion();
      });
    }
  }

  // Модальный квиз из урока
  function openModalQuiz(q) {
    const modal = document.getElementById("modal-quiz");
    const body = document.getElementById("modal-quiz-body");
    const title = document.getElementById("modal-quiz-title");
    if (!modal || !body) return;

    title.textContent = q.title;
    body.innerHTML = `
      <p style="margin-bottom: 12px;"><strong>${q.question}</strong></p>
      <div class="options-list">
        ${q.options.map((opt, idx) => `
          <button class="option-btn modal-opt" data-idx="${idx}">${opt}</button>
        `).join("")}
      </div>
      <div id="modal-expl" style="margin-top: 14px;"></div>
    `;

    body.querySelectorAll(".modal-opt").forEach(btn => {
      btn.addEventListener("click", () => {
        const chosen = parseInt(btn.getAttribute("data-idx"));
        const isCor = chosen === q.correctIndex;
        body.querySelectorAll(".modal-opt").forEach(b => b.disabled = true);

        if (isCor) {
          btn.classList.add("correct");
          addXP(50);
          saveUserProfile();
          updateUserStatsUI();
        } else {
          btn.classList.add("wrong");
          body.querySelectorAll(".modal-opt")[q.correctIndex].classList.add("correct");
        }

        const expl = document.getElementById("modal-expl");
        if (expl) {
          expl.innerHTML = `
            <div class="explanation-card ${isCor ? "success" : "failure"}">
              <h4>${isCor ? "✓ ВЕРНО! (+50 XP)" : "❌ ОШИБКА!"}</h4>
              <p style="margin: 6px 0;"><strong>Разбор:</strong> ${q.explanation}</p>
              ${q.interviewNote ? `<p style="margin-top: 6px; color: var(--accent-yellow);"><strong>💡 Заметка для собеседования:</strong> ${q.interviewNote}</p>` : ''}
              <div style="display: flex; gap: 10px; margin-top: 14px; border-top: 1px solid var(--border-color); padding-top: 10px;">
                <button id="btn-modal-next-lesson" class="btn btn-primary">Следующий урок →</button>
                <button id="btn-modal-close-quiz" class="btn btn-outline">Закрыть окно</button>
              </div>
            </div>
          `;

          document.getElementById("btn-modal-next-lesson")?.addEventListener("click", () => {
            modal.classList.add("hidden");
            goToNextLesson();
          });

          document.getElementById("btn-modal-close-quiz")?.addEventListener("click", () => {
            modal.classList.add("hidden");
          });
        }
      });
    });

    modal.classList.remove("hidden");
  }

  document.getElementById("modal-close-btn")?.addEventListener("click", () => {
    document.getElementById("modal-quiz")?.classList.add("hidden");
  });

  // --- 8. Cheatsheet & Search ---
  function renderCheatsheet() {
    const grid = document.getElementById("ref-cards-grid");
    if (!grid) return;

    const cards = [
      { cmd: "git status", desc: "Диагностика рабочей копии и индекса", danger: false },
      { cmd: "git add .", desc: "Добавление всех изменений в Staging Area", danger: false },
      { cmd: "git commit -m \"...\"", desc: "Создание постоянного снимка истории", danger: false },
      { cmd: "git switch -c danil/имя", desc: "Создание новой изолированной ветки", danger: false },
      { cmd: "git pull", desc: "Скачивание и слияние изменений (fetch + merge)", danger: false },
      { cmd: "git push origin danil/имя", desc: "Отправка своей ветки на GitHub", danger: false },
      { cmd: "git merge --abort", desc: "Безопасная отмена слияния при конфликте", danger: false },
      { cmd: "git reflog", desc: "Журнал всех перемещений HEAD (спасение коммитов)", danger: false },
      { cmd: "git reset --hard", desc: "СТОП-СЛОВО! Стирает код без возможности возврата", danger: true },
      { cmd: "git push --force", desc: "СТОП-СЛОВО! Переписывает удаленную историю", danger: true },
      { cmd: "git rebase", desc: "СТОП-СЛОВО! Опасно в общих публичных ветках", danger: true }
    ];

    grid.innerHTML = cards.map(c => `
      <div class="ref-card">
        <h4>${c.cmd}</h4>
        <p>${c.desc}</p>
        ${c.danger ? '<span class="ref-danger">⛔ СТОП-СЛОВО АНДРЕЯ</span>' : ''}
      </div>
    `).join("");

    document.getElementById("ref-filter")?.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      grid.querySelectorAll(".ref-card").forEach(card => {
        card.style.display = card.textContent.toLowerCase().includes(q) ? "block" : "none";
      });
    });
  }

  // --- 9. Profile & Persistence ---
  function normalizeProfile(p) {
    p.streakDays = p.streakDays || 0;
    p.lastVisitDay = p.lastVisitDay || "";
    p.dailyLog = Array.isArray(p.dailyLog) ? p.dailyLog : [];
    p.dailyChecks = p.dailyChecks && typeof p.dailyChecks === "object" ? p.dailyChecks : {};
    return p;
  }

  function loadUserProfile() {
    let data = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) data = JSON.parse(raw);
    } catch (e) {}
    return normalizeProfile(data || {
      xp: 0,
      completedLessons: [],
      answeredQuestions: [],
      competencies: { git: 0, pr: 0, qa: 0, cicd: 0, sec: 0, culture: 0 }
    });
  }

  function saveUserProfile() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(userProfile));
    } catch (e) {}
    writeProgressFile();
  }

  // --- 9.1 Ежедневная серия и автосохранение в файл ---
  function todayStr(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function touchDailyStreak() {
    const today = todayStr(new Date());
    if (userProfile.lastVisitDay === today) return;
    const yesterday = todayStr(new Date(Date.now() - 86400000));
    userProfile.streakDays = userProfile.lastVisitDay === yesterday ? userProfile.streakDays + 1 : 1;
    userProfile.lastVisitDay = today;
    userProfile.dailyLog.push(today);
    if (userProfile.dailyLog.length > 365) userProfile.dailyLog = userProfile.dailyLog.slice(-365);
    saveUserProfile();
    updateUserStatsUI();
  }

  let progressFileHandle = null;

  async function writeProgressFile() {
    if (!progressFileHandle) return;
    try {
      const writable = await progressFileHandle.createWritable();
      await writable.write(JSON.stringify(userProfile, null, 2));
      await writable.close();
    } catch (e) {
      progressFileHandle = null;
      updateAutoSaveUI();
    }
  }

  async function bindProgressFile() {
    if (!window.showSaveFilePicker) {
      alert("Этот браузер не умеет писать в файл напрямую. Открой игру в Chrome или Edge — или пользуйся кнопками 📥 Экспорт / 📤 Импорт.");
      return;
    }
    try {
      progressFileHandle = await window.showSaveFilePicker({
        suggestedName: "progress.json",
        types: [{ description: "JSON прогресса", accept: { "application/json": [".json"] } }]
      });
      updateAutoSaveUI();
      writeProgressFile();
    } catch (e) { /* пользователь отменил выбор файла */ }
  }

  function updateAutoSaveUI() {
    const btn = document.getElementById("btn-bind-file");
    if (btn) btn.textContent = progressFileHandle ? "✅ Автосейв: progress.json" : "🔗 Автосейв в файл";
  }

  // --- 9.2 Чек-лист рабочего дня (памятка) ---
  const DAILY_ITEMS = 5;

  function renderDailyRitual() {
    const dateEl = document.getElementById("daily-date-label");
    const progressEl = document.getElementById("daily-progress-label");
    const boxes = [];
    for (let i = 0; i < DAILY_ITEMS; i++) boxes.push(document.getElementById("dchk-" + i));
    if (!dateEl || boxes.some(b => !b)) return;

    const today = todayStr(new Date());
    const state = userProfile.dailyChecks[today] || new Array(DAILY_ITEMS).fill(false);
    userProfile.dailyChecks[today] = state;

    const days = ["воскресенье", "понедельник", "вторник", "среда", "четверг", "пятница", "суббота"];
    dateEl.textContent = `Сегодня: ${today} (${days[new Date().getDay()]})`;

    boxes.forEach((b, i) => {
      b.checked = !!state[i];
      b.onchange = () => {
        state[i] = b.checked;
        saveUserProfile();
        updateDailyProgress(boxes, progressEl);
      };
    });
    updateDailyProgress(boxes, progressEl);

    const mini = document.getElementById("daily-mini");
    if (mini) {
      mini.style.cursor = "pointer";
      mini.title = "Открыть чек-лист рабочего дня";
      mini.onclick = () => {
        const tabBtn = document.querySelector('.tab-btn[data-tab="tab-cheatsheet"]');
        if (tabBtn) tabBtn.click();
      };
    }
  }

  function updateDailyProgress(boxes, progressEl) {
    const done = boxes.filter(b => b.checked).length;
    if (progressEl) {
      progressEl.textContent = done >= DAILY_ITEMS
        ? "🎉 День закрыт! Серия растёт — так держать."
        : `День: ${done}/${DAILY_ITEMS}`;
    }
    const mini = document.getElementById("daily-mini");
    if (mini) mini.textContent = `${done}/${DAILY_ITEMS}`;
  }

  function addXP(amount) {
    userProfile.xp = Math.max(0, userProfile.xp + amount);
  }

  function updateUserStatsUI() {
    const xpEl = document.getElementById("user-xp");
    const lvlEl = document.getElementById("user-level");
    const readEl = document.getElementById("user-readiness");

    if (xpEl) xpEl.textContent = userProfile.xp;

    let levelTitle = "Новичок";
    if (userProfile.xp > 1200) levelTitle = "Senior / Готов к бою";
    else if (userProfile.xp > 600) levelTitle = "Инженер-разработчик";
    else if (userProfile.xp > 200) levelTitle = "Младший специалист";

    if (lvlEl) lvlEl.textContent = levelTitle;

    // Готовность к собеседованию (0 - 100%)
    const compVals = Object.values(userProfile.competencies);
    const avgComp = compVals.reduce((a, b) => a + b, 0) / compVals.length;
    const readiness = Math.round(avgComp);
    if (readEl) readEl.textContent = `${readiness}%`;

    const streakEl = document.getElementById("user-streak");
    if (streakEl) streakEl.textContent = `🔥 ${userProfile.streakDays || 0} дн.`;

    // Полоски компетенций
    const setWidth = (id, val) => {
      const bar = document.getElementById(id);
      if (bar) bar.style.width = `${val}%`;
    };
    setWidth("comp-git", userProfile.competencies.git);
    setWidth("comp-pr", userProfile.competencies.pr);
    setWidth("comp-qa", userProfile.competencies.qa);
    setWidth("comp-cicd", userProfile.competencies.cicd);
    setWidth("comp-sec", userProfile.competencies.sec);
    setWidth("comp-culture", userProfile.competencies.culture || 0);
  }

  // Экспорт / Импорт / Сброс
  document.getElementById("btn-bind-file")?.addEventListener("click", bindProgressFile);
  document.getElementById("btn-export-profile")?.addEventListener("click", () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(userProfile, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", "devops_quest_profile.json");
    dlAnchor.click();
  });

  document.getElementById("btn-import-profile")?.addEventListener("click", () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          userProfile = normalizeProfile(JSON.parse(event.target.result));
          saveUserProfile();
          updateUserStatsUI();
          renderCurriculum();
          alert("Профиль успешно импортирован!");
        } catch (err) {
          alert("Ошибка чтения файла JSON.");
        }
      };
      reader.readAsText(file);
    };
    input.click();
  });

  document.getElementById("btn-reset-profile")?.addEventListener("click", () => {
    if (confirm("Вы уверены, что хотите сбросить весь прогресс обучения?")) {
      userProfile = {
        xp: 0,
        completedLessons: [],
        answeredQuestions: [],
        competencies: { git: 0, pr: 0, qa: 0, cicd: 0, sec: 0, culture: 0 },
        streakDays: 0,
        lastVisitDay: "",
        dailyLog: [],
        dailyChecks: {}
      };
      saveUserProfile();
      updateUserStatsUI();
      renderCurriculum();
    }
  });
});
