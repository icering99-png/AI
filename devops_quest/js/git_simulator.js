// devops_quest/js/git_simulator.js — Интерактивный виртуальный эмулятор Git с графом и Сторожем Андрея

class GitSimulator {
  constructor() {
    this.resetState();
  }

  resetState() {
    this.currentBranch = "main";
    this.head = "c2";
    this.isDetached = false;
    this.branches = {
      "main": ["c1", "c2"],
      "danil/tariffs": ["c1", "c2"]
    };
    this.commits = {
      "c1": { hash: "3a91f0a", msg: "Инициализация проекта чат-бота для сайта", author: "Андрей", parent: null },
      "c2": { hash: "8b41c2d", msg: "Базовый шлюз маскировки персональных данных", author: "Андрей", parent: "c1" }
    };
    this.workingTree = [
      { name: "answers.py", status: "modified" },
      { name: "tariffs.md", status: "untracked" }
    ];
    this.stagingArea = [];
    this.remoteBranches = {
      "origin/main": ["c1", "c2"]
    };
    this.reflog = [
      { hash: "8b41c2d", action: "commit: Базовый шлюз маскировки", head: "HEAD@{0}" },
      { hash: "3a91f0a", action: "commit (initial): Инициализация проекта", head: "HEAD@{1}" }
    ];
    this.safetyAlerts = [];
  }

  // Проверка стоп-слов Андрея
  checkAndreyStopWords(cmd) {
    const raw = cmd.trim();
    const stopPatterns = [
      { regex: /--force\b|-f\b/, word: "--force / -f", reason: "Переписывание удаленной истории! Может уничтожить коммиты коллег." },
      { regex: /reset\s+--hard\b/, word: "reset --hard", reason: "Уничтожает незакоммиченные файлы и код в рабочей директории без возможности отмены!" },
      { regex: /clean\s+-fd?\b/, word: "git clean", reason: "Безвозвратно удаляет новые неотслеживаемые файлы проекта." },
      { regex: /branch\s+-D\b/, word: "branch -D", reason: "Принудительное удаление ветки без проверки слияния." },
      { regex: /push\s+.*origin\s+main\b/, word: "push origin main", reason: "Прямой пуш в main строго запрещен! Вся работа идет только через ветку danil/... и Pull Request." },
      { regex: /rebase\b/, word: "rebase", reason: "Перебазирование переписывает хеши коммитов. В командной работе используйте безопасный merge." },
      { regex: /\.git\b/, word: "удаление .git", reason: "Удаление скрытой памяти репозитория!" }
    ];

    for (const item of stopPatterns) {
      if (item.regex.test(raw)) {
        return item;
      }
    }
    return null;
  }

  execute(cmdStr) {
    const trimmed = cmdStr.trim();
    if (!trimmed) return { out: "", type: "info" };

    // Проверка Сторожа Андрея
    const stopWordMatch = this.checkAndreyStopWords(trimmed);
    if (stopWordMatch) {
      const alertMsg = `⛔ СТОРОЖ АНДРЕЯ ЗАБЛОКИРОВАЛ КОМАНДУ!\n` +
        `Обнаружено опасное стоп-слово: [${stopWordMatch.word}]\n` +
        `Причина блокировки: ${stopWordMatch.reason}\n` +
        `Правило: В Antigravity всегда жми "Reject" на такие предложения от ИИ!`;
      this.safetyAlerts.unshift(alertMsg);
      return {
        out: alertMsg,
        type: "error"
      };
    }

    if (!trimmed.startsWith("git")) {
      return { out: `bash: ${trimmed.split(" ")[0]}: команда не найдена. Доступны команды git.`, type: "error" };
    }

    const parts = trimmed.split(/\s+/);
    const subCmd = parts[1];

    switch (subCmd) {
      case "status":
        return this.cmdStatus();
      case "add":
        return this.cmdAdd(parts.slice(2));
      case "commit":
        return this.cmdCommit(parts.slice(2));
      case "branch":
        return this.cmdBranch(parts.slice(2));
      case "switch":
      case "checkout":
        return this.cmdSwitch(parts.slice(2));
      case "log":
        return this.cmdLog(parts.slice(2));
      case "diff":
        return this.cmdDiff(parts.slice(2));
      case "push":
        return this.cmdPush(parts.slice(2));
      case "pull":
        return this.cmdPull(parts.slice(2));
      case "reflog":
        return this.cmdReflog();
      case "merge":
        return this.cmdMerge(parts.slice(2));
      case "help":
        return {
          out: "Поддерживаемые команды:\n  git status\n  git add <файл | .>\n  git commit -m \"сообщение\"\n  git branch [имя]\n  git switch [-c имя]\n  git log [--oneline]\n  git diff [--staged]\n  git push [origin ветка]\n  git pull\n  git reflog",
          type: "info"
        };
      default:
        return { out: `git: '${subCmd}' не поддерживается в виртуальном тренажере. Попробуйте 'git help'.`, type: "warning" };
    }
  }

  cmdStatus() {
    let lines = [];
    if (this.isDetached) {
      lines.push(`ВНИМАНИЕ: HEAD оторван на коммите ${this.head}`);
    } else {
      lines.push(`На ветке ${this.currentBranch}`);
      const localCommits = this.branches[this.currentBranch] || [];
      const remoteCommits = this.remoteBranches[`origin/${this.currentBranch}`] || [];
      const unpushed = localCommits.length - remoteCommits.length;
      if (unpushed > 0) {
        lines.push(`Ваша ветка опережает 'origin/${this.currentBranch}' на ${unpushed} коммит(а).`);
        lines.push(`  (используйте "git push", чтобы опубликовать локальные коммиты)`);
      } else {
        lines.push(`Ваша ветка обновлена в соответствии с 'origin/${this.currentBranch}'.`);
      }
    }

    lines.push("");
    if (this.stagingArea.length > 0) {
      lines.push("Изменения, которые войдут в коммит:");
      lines.push('  (используйте "git restore --staged <файл>...", чтобы убрать из индекса)');
      for (const f of this.stagingArea) {
        lines.push(`\t\x1b[32mновый/изменен: ${f.name}\x1b[0m`);
      }
      lines.push("");
    }

    const modified = this.workingTree.filter(f => f.status === "modified");
    if (modified.length > 0) {
      lines.push("Изменения, которые не подготовлены для коммита:");
      lines.push('  (используйте "git add <файл>...", чтобы добавить в индекс)');
      for (const f of modified) {
        lines.push(`\t\x1b[31mизменено:     ${f.name}\x1b[0m`);
      }
      lines.push("");
    }

    const untracked = this.workingTree.filter(f => f.status === "untracked");
    if (untracked.length > 0) {
      lines.push("Неотслеживаемые файлы:");
      lines.push('  (используйте "git add <файл>...", чтобы включить в коммит)');
      for (const f of untracked) {
        lines.push(`\t\x1b[31m${f.name}\x1b[0m`);
      }
      lines.push("");
    }

    if (this.stagingArea.length === 0 && this.workingTree.length === 0) {
      lines.push("Рабочий каталог чист, нечего коммитить.");
    }

    return { out: lines.join("\n"), type: "info" };
  }

  cmdAdd(args) {
    if (args.length === 0) {
      return { out: "Ничего не указано, ничего не добавлено.", type: "warning" };
    }
    const target = args[0];
    if (target === "." || target === "-A") {
      this.stagingArea = [...this.stagingArea, ...this.workingTree];
      this.workingTree = [];
      return { out: "Все файлы добавлены в Staging Area.", type: "success" };
    }

    const foundIdx = this.workingTree.findIndex(f => f.name === target);
    if (foundIdx !== -1) {
      const item = this.workingTree.splice(foundIdx, 1)[0];
      this.stagingArea.push(item);
      return { out: `Файл '${target}' добавлен в Staging Area.`, type: "success" };
    }

    return { out: `fatal: путь '${target}' не соответствует ни одному файлу`, type: "error" };
  }

  cmdCommit(args) {
    if (this.stagingArea.length === 0) {
      return { out: "В индексе нет изменений для коммита (используйте \"git add\").", type: "warning" };
    }

    let msg = "Автоматический коммит";
    const mIdx = args.indexOf("-m");
    if (mIdx !== -1 && args[mIdx + 1]) {
      msg = args.slice(mIdx + 1).join(" ").replace(/['"]/g, "");
    }

    const newId = "c" + (Object.keys(this.commits).length + 1);
    const shortHash = Math.random().toString(16).substring(2, 9);
    
    this.commits[newId] = {
      hash: shortHash,
      msg: msg,
      author: "Данил",
      parent: this.head
    };

    if (!this.branches[this.currentBranch]) {
      this.branches[this.currentBranch] = [];
    }
    this.branches[this.currentBranch].push(newId);
    this.head = newId;

    this.reflog.unshift({
      hash: shortHash,
      action: `commit: ${msg}`,
      head: `HEAD@{0}`
    });

    const count = this.stagingArea.length;
    this.stagingArea = [];

    return {
      out: `[${this.currentBranch} ${shortHash}] ${msg}\n ${count} файл(ов) изменено`,
      type: "success"
    };
  }

  cmdBranch(args) {
    if (args.length === 0) {
      const lines = Object.keys(this.branches).map(b => (b === this.currentBranch ? `* \x1b[32m${b}\x1b[0m` : `  ${b}`));
      return { out: lines.join("\n"), type: "info" };
    }

    const newName = args[0];
    if (this.branches[newName]) {
      return { out: `fatal: Ветка с именем '${newName}' уже существует.`, type: "error" };
    }

    this.branches[newName] = [...(this.branches[this.currentBranch] || [])];
    return { out: `Создана ветка '${newName}'. Переключитесь на нее командой: git switch ${newName}`, type: "success" };
  }

  cmdSwitch(args) {
    if (args.length === 0) {
      return { out: "Укажите имя ветки.", type: "warning" };
    }

    if (args[0] === "-c" || args[0] === "-b") {
      const branchName = args[1];
      if (!branchName) return { out: "Укажите имя новой ветки.", type: "error" };
      this.cmdBranch([branchName]);
      this.currentBranch = branchName;
      this.isDetached = false;
      return { out: `Переключились на новую ветку '${branchName}'`, type: "success" };
    }

    const targetBranch = args[0];
    if (this.branches[targetBranch]) {
      this.currentBranch = targetBranch;
      this.head = this.branches[targetBranch][this.branches[targetBranch].length - 1];
      this.isDetached = false;
      return { out: `Переключились на ветку '${targetBranch}'`, type: "success" };
    }

    return { out: `error: путь к ветке '${targetBranch}' не найден.`, type: "error" };
  }

  cmdLog(args) {
    const list = this.branches[this.currentBranch] || [];
    if (list.length === 0) return { out: "История пуста.", type: "info" };

    const isOneLine = args.includes("--oneline");
    const reversed = [...list].reverse();

    if (isOneLine) {
      const lines = reversed.map(cid => {
        const c = this.commits[cid];
        const isHead = cid === this.head ? " (HEAD -> " + this.currentBranch + ")" : "";
        return `${c.hash}${isHead} ${c.msg}`;
      });
      return { out: lines.join("\n"), type: "info" };
    }

    const lines = reversed.map(cid => {
      const c = this.commits[cid];
      return `commit ${c.hash} (HEAD -> ${this.currentBranch})\nАвтор:  ${c.author}\nДата:   ${new Date().toLocaleDateString()}\n\n    ${c.msg}\n`;
    });
    return { out: lines.join("\n"), type: "info" };
  }

  cmdDiff(args) {
    if (args.includes("--staged") || args.includes("--cached")) {
      if (this.stagingArea.length === 0) return { out: "Индекс пуст.", type: "info" };
      return {
        out: `diff --git a/answers.py b/answers.py\n--- a/answers.py\n+++ b/answers.py\n@@ -10,3 +10,6 @@\n+def get_tariff_answer(query):\n+    # Возвращает базовые тарифы для МТС\n+    return "Базовый тариф: 150-220 тыс руб."`,
        type: "success"
      };
    }

    if (this.workingTree.length === 0) return { out: "Рабочая копия совпадает с индексом.", type: "info" };
    return {
      out: `diff --git a/answers.py b/answers.py\n--- a/answers.py\n+++ b/answers.py\n@@ -1,3 +1,3 @@\n-greeting = "Здравствуйте!"\n+greeting = "Здравствуйте! Чем я могу вам помочь?"`,
      type: "warning"
    };
  }

  cmdPush(args) {
    if (this.currentBranch === "main") {
      return {
        out: "⛔ ОШИБКА: Прямой push в main отклонен защитой репозитория (Branch Protection)!\nОткройте Pull Request из своей ветки danil/...",
        type: "error"
      };
    }

    this.remoteBranches[`origin/${this.currentBranch}`] = [...this.branches[this.currentBranch]];
    return {
      out: `Все коммиты ветки '${this.currentBranch}' успешно отправлены на GitHub (origin/${this.currentBranch}).\nТеперь перейдите во вкладку 'Pull Request', чтобы отдать работу Андрею.`,
      type: "success"
    };
  }

  cmdPull() {
    return {
      out: "Уже обновлено (Already up to date). Все свежие коммиты Андрея синхронизированы.",
      type: "success"
    };
  }

  cmdReflog() {
    const lines = this.reflog.map(item => `${item.hash} ${item.head}: ${item.action}`);
    return { out: lines.join("\n"), type: "info" };
  }

  cmdMerge(args) {
    return {
      out: "Для безопасного слияния используйте графический симулятор во вкладке 'Pull Request и Конфликты'.",
      type: "warning"
    };
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { GitSimulator };
}
