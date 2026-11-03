const API_URL = "/chat";

const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const messagesContainer = document.getElementById("messagesContainer");
const welcomeScreen = document.getElementById("welcomeScreen");
const chatHistory = document.getElementById("chatHistory");

const sidebar = document.getElementById("sidebar");
const menuButton = document.getElementById("menuButton");
const closeSidebar = document.getElementById("closeSidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");
const newChatButton = document.getElementById("newChatButton");

let conversations = [];
let activeConversationId = null;
let isLoading = false;


// -----------------------------
// Conversation management
// -----------------------------

function createConversation() {
    const conversation = {
        id: Date.now(),
        title: "محادثة جديدة",
        messages: []
    };

    conversations.unshift(conversation);
    activeConversationId = conversation.id;

    renderMessages();
    renderHistory();
    closeMobileSidebar();

    return conversation;
}


function getActiveConversation() {
    return conversations.find(
        conversation => conversation.id === activeConversationId
    );
}


function renderHistory() {
    chatHistory.innerHTML = "";

    if (conversations.length === 0) {
        chatHistory.innerHTML =
            '<div class="empty-history">لا توجد محادثات سابقة</div>';
        return;
    }

    conversations.forEach(conversation => {
        const item = document.createElement("div");

        item.className = "history-item";
        item.textContent = conversation.title;
        item.title = conversation.title;

        if (conversation.id === activeConversationId) {
            item.style.background = "var(--surface-hover)";
            item.style.color = "white";
        }

        item.addEventListener("click", () => {
            activeConversationId = conversation.id;
            renderMessages();
            renderHistory();
            closeMobileSidebar();
        });

        chatHistory.appendChild(item);
    });
}


function renderMessages() {
    const conversation = getActiveConversation();

    messagesContainer.innerHTML = "";

    const hasMessages =
        conversation && conversation.messages.length > 0;

    welcomeScreen.classList.toggle("hidden", hasMessages);

    if (!conversation) return;

    conversation.messages.forEach(message => {
        addMessageToDOM(
            message.role,
            message.content,
            message.meta
        );
    });

    scrollToBottom();
}


function updateConversationTitle(conversation, question) {
    if (conversation.title !== "محادثة جديدة") return;

    conversation.title =
        question.length > 30
            ? question.slice(0, 30) + "..."
            : question;

    renderHistory();
}


// -----------------------------
// Message rendering
// -----------------------------

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function renderInlineMarkdown(value) {
    let text = escapeHTML(value);
    text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
    text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
        (_match, label, url) =>
            `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`
    );
    text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/__(.+?)__/g, "<strong>$1</strong>");
    text = text.replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, "$1<em>$2</em>");
    text = text.replace(/(^|[^_])_([^_\n]+)_(?!_)/g, "$1<em>$2</em>");
    return text;
}

function normalizeAssistantText(markdown) {
    return String(markdown ?? "")
        // Some model responses contain escaped newline characters instead of real line breaks.
        .replace(/\\r\\n/g, "\n")
        .replace(/\\n/g, "\n")
        .replace(/\r\n?/g, "\n")
        // Clean common space entities sometimes emitted by the model.
        .replace(/&amp;#x20;|&#x20;|&#32;|&nbsp;/gi, " ")
        .replace(/&amp;nbsp;/gi, " ")
        .trim();
}

function renderMarkdown(markdown) {
    const normalizedMarkdown = normalizeAssistantText(markdown)
        .replace(/\\([*_#`])/g, "$1");
    const lines = normalizedMarkdown.split("\n");
    const output = [];
    let paragraph = [];
    let listType = null;
    let listItems = [];
    let inCode = false;
    let codeLines = [];
    let tableLines = [];

    const flushParagraph = () => {
        if (!paragraph.length) return;
        output.push(`<p>${paragraph.map(renderInlineMarkdown).join("<br>")}</p>`);
        paragraph = [];
    };

    const flushList = () => {
        if (!listItems.length) return;
        const tag = listType === "ol" ? "ol" : "ul";
        output.push(`<${tag}>${listItems.map(item =>
            `<li>${renderInlineMarkdown(item)}</li>`
        ).join("")}</${tag}>`);
        listItems = [];
        listType = null;
    };

    const flushTable = () => {
        if (!tableLines.length) return;
        const rows = tableLines
            .filter(line => !/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line))
            .map(line => line.trim().replace(/^\|/, "").replace(/\|$/, "")
                .split("|").map(cell => cell.trim()));
        if (rows.length) {
            const [header, ...body] = rows;
            output.push(
                `<div class="markdown-table-wrap"><table><thead><tr>${header.map(cell =>
                    `<th>${renderInlineMarkdown(cell)}</th>`
                ).join("")}</tr></thead><tbody>${body.map(row =>
                    `<tr>${row.map(cell => `<td>${renderInlineMarkdown(cell)}</td>`).join("")}</tr>`
                ).join("")}</tbody></table></div>`
            );
        }
        tableLines = [];
    };

    for (const line of lines) {
        if (line.trim().startsWith("```")) {
            flushParagraph(); flushList(); flushTable();
            if (inCode) {
                output.push(`<pre><code>${escapeHTML(codeLines.join("\n"))}</code></pre>`);
                codeLines = [];
                inCode = false;
            } else {
                inCode = true;
            }
            continue;
        }

        if (inCode) {
            codeLines.push(line);
            continue;
        }

        if (!line.trim()) {
            flushParagraph(); flushList(); flushTable();
            continue;
        }

        if (/^\s*\|.*\|\s*$/.test(line)) {
            flushParagraph(); flushList();
            tableLines.push(line);
            continue;
        } else {
            flushTable();
        }

        const heading = line.match(/^\s*(#{1,4})\s+(.+)$/);
        if (heading) {
            flushParagraph(); flushList();
            const level = Math.min(heading[1].length + 1, 5);
            output.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
            continue;
        }

        if (/^\s*([-*_]\s*){3,}$/.test(line)) {
            flushParagraph(); flushList();
            output.push("<hr>");
            continue;
        }

        const unordered = line.match(/^\s*[-*+]\s+(.+)$/);
        const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
        if (unordered || ordered) {
            flushParagraph();
            const nextType = ordered ? "ol" : "ul";
            if (listType && listType !== nextType) flushList();
            listType = nextType;
            listItems.push((unordered || ordered)[1]);
            continue;
        }

        flushList();

        const quote = line.match(/^\s*>\s?(.*)$/);
        if (quote) {
            flushParagraph();
            output.push(`<blockquote>${renderInlineMarkdown(quote[1])}</blockquote>`);
            continue;
        }

        paragraph.push(line);
    }

    flushParagraph();
    flushList();
    flushTable();

    if (inCode) {
        output.push(`<pre><code>${escapeHTML(codeLines.join("\n"))}</code></pre>`);
    }

    return output.join("");
}


function renderMarkdownCards(markdown) {
    const normalized = normalizeAssistantText(markdown);
    const lines = normalized.split("\n");
    const sections = [];
    let current = { title: "", body: [] };

    const flush = () => {
        if (current.title || current.body.some(line => line.trim())) {
            sections.push(current);
        }
        current = { title: "", body: [] };
    };

    const ordinalHeading = /^(?:أولًا|أولا|ثانيًا|ثانيا|ثالثًا|ثالثا|رابعًا|رابعا|خامسًا|خامسا|سادسًا|سادسا|سابعًا|سابعا|ثامنًا|ثامنا)\s*[:：]\s*(.+)$/;

    for (const line of lines) {
        const markdownHeading = line.match(/^##\s+(.+)$/);
        const ordinalMatch = line.match(ordinalHeading);
        const boldHeading = line.match(
            /^\*\*((?:أولًا|أولا|ثانيًا|ثانيا|ثالثًا|ثالثا|رابعًا|رابعا|خامسًا|خامسا|سادسًا|سادسا|سابعًا|سابعا|ثامنًا|ثامنا)\s*[:：]\s*.+|.{2,90}[:：])\*\*$/
        ) || line.match(/^\*\*(.{2,90}?)\*\*\s*[:：]$/);

        if (markdownHeading || ordinalMatch || boldHeading) {
            flush();
            current.title = (markdownHeading?.[1] || ordinalMatch?.[1] || boldHeading?.[1] || "").trim();
        } else {
            current.body.push(line);
        }
    }
    flush();

    if (!sections.length) {
        return `<div class="answer-cards"><section class="answer-card">${renderMarkdown(normalized)}</section></div>`;
    }

    // Keep a leading summary/title with the first content card instead of creating an empty card.
    if (sections.length > 1 && !sections[0].title && sections[0].body.join("").trim()) {
        const intro = sections.shift();
        sections[0].body.unshift(...intro.body, "");
    }

    return `<div class="answer-cards">${sections.map(section => {
        const title = section.title
            ? `<h3 class="answer-card-title">${renderInlineMarkdown(section.title)}</h3>`
            : "";
        const body = renderMarkdown(section.body.join("\n"));
        return `<section class="answer-card">${title}${body}</section>`;
    }).join("")}</div>`;
}


function addMessageToDOM(role, content, meta = "") {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "أنت" : "S";

    const body = document.createElement("div");

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";

    // User messages remain plain text. Assistant messages support safe Markdown.
    if (role === "assistant") {
        messageContent.classList.add("markdown-body");
        messageContent.innerHTML = renderMarkdownCards(content);
    } else {
        messageContent.textContent = content;
    }

    body.appendChild(messageContent);

    if (meta) {
        const metadata = document.createElement("div");
        metadata.className = "message-meta";
        metadata.textContent = meta;
        body.appendChild(metadata);
    }

    message.appendChild(avatar);
    message.appendChild(body);

    messagesContainer.appendChild(message);

    return message;
}


function addTypingIndicator() {
    const message = document.createElement("div");
    message.className = "message assistant";
    message.id = "typingIndicator";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "S";

    const content = document.createElement("div");
    content.className = "message-content";

    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";

    for (let i = 0; i < 3; i++) {
        indicator.appendChild(document.createElement("span"));
    }

    content.appendChild(indicator);
    message.appendChild(avatar);
    message.appendChild(content);

    messagesContainer.appendChild(message);

    scrollToBottom();
}


function removeTypingIndicator() {
    const indicator = document.getElementById("typingIndicator");

    if (indicator) {
        indicator.remove();
    }
}


function scrollToBottom() {
    const chatArea = document.getElementById("chatArea");

    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}


// -----------------------------
// Send message to FastAPI
// -----------------------------

async function sendMessage(question = null) {
    if (isLoading) return;

    const text = (question || questionInput.value).trim();

    if (!text) return;

    if (!activeConversationId) {
        createConversation();
    }

    const conversation = getActiveConversation();

    conversation.messages.push({
        role: "user",
        content: text
    });

    updateConversationTitle(conversation, text);

    questionInput.value = "";
    autoResizeInput();
    updateSendButton();

    renderMessages();

    isLoading = true;
    updateSendButton();
    addTypingIndicator();

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: text,
                session_id: String(conversation.id),
                n_results: 5
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));

            throw new Error(
                errorData.detail || `HTTP Error ${response.status}`
            );
        }

        const data = await response.json();

        const meta = [
            data.generation_mode === "gemini"
                ? "Gemini AI"
                : "Local Response",
            `عدد المستندات النصية المسترجعة: ${data.evidence_count ?? 0}`,
            data.compound ? `المشروع: ${data.compound}` : null
        ].filter(Boolean).join(" • ");

        conversation.messages.push({
            role: "assistant",
            content: data.answer,
            meta: meta
        });

    } catch (error) {
        console.error("Chat API error:", error);

        conversation.messages.push({
            role: "assistant",
            content:
                "حصلت مشكلة أثناء الاتصال بالمساعد.\n\n" +
                "تأكدي أن الـ API يعمل على المنفذ 8001، ثم حاولي مرة أخرى.\n\n" +
                `تفاصيل الخطأ: ${error.message}`
        });

    } finally {
        isLoading = false;

        removeTypingIndicator();
        renderMessages();
        updateSendButton();
    }
}


// -----------------------------
// Input controls
// -----------------------------

function updateSendButton() {
    sendButton.disabled =
        isLoading || !questionInput.value.trim();
}


function autoResizeInput() {
    questionInput.style.height = "auto";

    questionInput.style.height =
        Math.min(questionInput.scrollHeight, 150) + "px";
}


questionInput.addEventListener("input", () => {
    autoResizeInput();
    updateSendButton();
});


questionInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});


sendButton.addEventListener("click", () => {
    sendMessage();
});


// -----------------------------
// Suggested questions
// -----------------------------

document.querySelectorAll(".suggestion-card").forEach(card => {
    card.addEventListener("click", () => {
        const question = card.dataset.question;

        if (question) {
            sendMessage(question);
        }
    });
});


// -----------------------------
// Sidebar controls
// -----------------------------

function openMobileSidebar() {
    sidebar.classList.add("open");
    sidebarOverlay.classList.add("show");
}


function closeMobileSidebar() {
    sidebar.classList.remove("open");
    sidebarOverlay.classList.remove("show");
}


menuButton.addEventListener("click", openMobileSidebar);

closeSidebar.addEventListener("click", closeMobileSidebar);

sidebarOverlay.addEventListener("click", closeMobileSidebar);


newChatButton.addEventListener("click", () => {
    createConversation();
});


// -----------------------------
// Initial setup
// -----------------------------

createConversation();
updateSendButton();
