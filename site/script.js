const i18n = {
    zh: {
        page_title: "SFTLab | SFT/LLM 本地工具集",
        toggle: "中文 / EN",
        aria_label: "切换到英文",
        nav_features: "功能",
        nav_workflow: "流程",
        nav_about: "关于",
        hero_badge: "SFT Desktop Toolkit",
        hero_title: "聚焦 SFT/LLM 高频任务的本地工具集",
        hero_desc: "基于 Python + PySide6，集中管理参数模板、Prompt、Token 统计、JSON/Diff 处理与 API 测试，减少多工具切换成本。",
        hero_primary: "开始了解",
        hero_secondary: "查看流程",
        hero_note: "Local-first. Productive. Reliable.",
        feature_title: "功能模块",
        feature_1_title: "参数管理",
        feature_1_desc: "保存与编辑 SFT CLI 参数模板，支持版本记录与基础校验。",
        feature_2_title: "Prompt 管理",
        feature_2_desc: "按目录分类维护 Prompt，支持 CRUD 与历史版本管理。",
        feature_3_title: "Token 统计",
        feature_3_desc: "支持 gpt、qwen、llama 三类模型的 Token 计数。",
        feature_4_title: "JSON 工具",
        feature_4_desc: "提供解析、格式化、压缩、转义/反转义与错误提示。",
        feature_5_title: "Diff 工具",
        feature_5_desc: "支持行级/字符级文本对比，并可进行 JSON/Prompt 归一化比较。",
        feature_6_title: "LLM API 测试",
        feature_6_desc: "支持 OpenAI 兼容接口请求与流式响应解析。",
        feature_7_title: "Calculator",
        feature_7_desc: "支持表达式计算、变量管理与历史记录。",
        feature_8_title: "Timer",
        feature_8_desc: "支持分段计时与历史会话记录。",
        workflow_title: "典型使用流程",
        workflow_1: "配置并保存 SFT 参数模板",
        workflow_2: "管理 Prompt 并完成版本迭代",
        workflow_3: "统计 Token，处理 JSON/Diff，并辅助计算与计时",
        workflow_4: "使用 LLM API 测试验证请求与响应",
        footer_text: "SFTLab · 一次构建，全球可用。"
    },
    en: {
        page_title: "SFTLab | SFT/LLM Desktop Toolkit",
        toggle: "中文 / EN",
        aria_label: "Switch to Chinese",
        nav_features: "Features",
        nav_workflow: "Workflow",
        nav_about: "About",
        hero_badge: "SFT Desktop Toolkit",
        hero_title: "A Local Toolkit for High-Frequency SFT/LLM Tasks",
        hero_desc: "Built with Python + PySide6 to centralize parameter templates, prompt management, token counting, JSON/Diff utilities, and LLM API testing.",
        hero_primary: "Get Started",
        hero_secondary: "View Workflow",
        hero_note: "Local-first. Productive. Reliable.",
        feature_title: "Tool Modules",
        feature_1_title: "Parameter Management",
        feature_1_desc: "Save and edit SFT CLI parameter templates with versioning and basic validation.",
        feature_2_title: "Prompt Management",
        feature_2_desc: "Organize prompts by folders with CRUD operations and version history.",
        feature_3_title: "Token Counter",
        feature_3_desc: "Count tokens for gpt, qwen, and llama model families.",
        feature_4_title: "JSON Utility",
        feature_4_desc: "Provide parsing, formatting, compression, escape/unescape, and error hints.",
        feature_5_title: "Diff Utility",
        feature_5_desc: "Support line/char diff and normalized comparison for JSON and prompts.",
        feature_6_title: "LLM API Tester",
        feature_6_desc: "Test OpenAI-compatible APIs with streaming response parsing.",
        feature_7_title: "Calculator",
        feature_7_desc: "Support expression calculation, variables, and history.",
        feature_8_title: "Timer",
        feature_8_desc: "Support segmented timing and session history.",
        workflow_title: "Typical Workflow",
        workflow_1: "Configure and save SFT parameter templates",
        workflow_2: "Manage prompts and iterate versions",
        workflow_3: "Count tokens, process JSON/diffs, and assist with calc/timing",
        workflow_4: "Validate requests and responses via LLM API tester",
        footer_text: "SFTLab · Build once, scale globally."
    }
};

const LANG_KEY = "site_lang";
const langToggle = document.getElementById("langToggle");

function detectInitialLang() {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved && i18n[saved]) {
        return saved;
    }

    const browserLang = navigator.language.toLowerCase();
    return browserLang.startsWith("zh") ? "zh" : "en";
}

function applyLanguage(lang) {
    const dict = i18n[lang];
    if (!dict) {
        return;
    }

    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";

    document.querySelectorAll("[data-i18n]").forEach((node) => {
        const key = node.getAttribute("data-i18n");
        if (dict[key]) {
            node.textContent = dict[key];
        }
    });

    langToggle.textContent = dict.toggle;
    langToggle.setAttribute("aria-label", dict.aria_label);
    localStorage.setItem(LANG_KEY, lang);
}

langToggle.addEventListener("click", () => {
    const current = localStorage.getItem(LANG_KEY) || detectInitialLang();
    const next = current === "zh" ? "en" : "zh";
    applyLanguage(next);
});

applyLanguage(detectInitialLang());
