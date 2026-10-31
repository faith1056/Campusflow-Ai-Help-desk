const TICKET_STATUSES = ["Open", "In progress", "Resolved"];

// Tickets from the most recent load, used by the detail view.
let loadedTickets = [];


// Check how many AI providers have API keys configured.
async function loadProviderStatus() {
    const statusElement = document.getElementById("provider-status");

    if (!statusElement) {
        return;
    }

    try {
        const response = await fetch("/api/provider-status");

        if (!response.ok) {
            throw new Error("Could not check provider status.");
        }

        const data = await response.json();

        statusElement.textContent =
            `${data.configured}/${data.total} Configured`;

    } catch (error) {
        console.error("Provider status check failed:", error);
        statusElement.textContent = "Unavailable";
    }
}


// Return the CSS class that matches a ticket status.
function statusClass(status) {
    if (status === "Resolved") {
        return "resolved";
    }

    if (status === "In progress") {
        return "in-progress";
    }

    return "open";
}


// Create one labelled section inside the ticket dialog.
function createDialogSection(label, text, className) {
    const section = document.createElement("section");
    section.className = "ticket-dialog-section";

    const heading = document.createElement("h3");
    heading.textContent = label;

    const body = document.createElement("p");
    body.className = className;
    body.textContent = text;

    section.append(heading, body);
    return section;
}


// Return the ticket detail dialog, creating it the first time.
function getTicketDialog() {
    let dialog = document.getElementById("ticket-dialog");

    if (dialog) {
        return dialog;
    }

    dialog = document.createElement("dialog");
    dialog.id = "ticket-dialog";
    dialog.className = "ticket-dialog";
    dialog.setAttribute("aria-labelledby", "ticket-dialog-title");

    // Clicking the dark backdrop closes the dialog.
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });

    document.body.appendChild(dialog);
    return dialog;
}


// Show the full details of a ticket.
function openTicketDialog(ticketId) {
    const ticket = loadedTickets.find((item) => item.id === ticketId);

    if (!ticket) {
        return false;
    }

    const dialog = getTicketDialog();
    dialog.replaceChildren();

    const header = document.createElement("div");
    header.className = "ticket-dialog-header";

    const titleGroup = document.createElement("div");

    const eyebrow = document.createElement("div");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = `TICKET ${ticket.id || "N/A"}`;

    const title = document.createElement("h2");
    title.id = "ticket-dialog-title";
    title.textContent = ticket.title || "Untitled";

    titleGroup.append(eyebrow, title);

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "secondary-button";
    closeButton.textContent = "Close";
    closeButton.addEventListener("click", () => dialog.close());

    header.append(titleGroup, closeButton);

    const meta = document.createElement("div");
    meta.className = "ticket-dialog-meta";

    const status = ticket.status || "Open";

    const providerTag = document.createElement("span");
    providerTag.className = "ticket-dialog-tag";
    providerTag.textContent = `AI provider: ${ticket.ai_provider || "N/A"}`;

    const statusTag = document.createElement("span");
    statusTag.className = `ticket-dialog-tag ${statusClass(status)}`;
    statusTag.textContent = `Status: ${status}`;

    meta.append(providerTag, statusTag);

    dialog.append(
        header,
        meta,
        createDialogSection(
            "Problem description",
            ticket.description || "No description saved.",
            "ticket-dialog-text"
        ),
        createDialogSection(
            "AI troubleshooting suggestions",
            ticket.ai_suggestions || "No AI suggestions saved.",
            "ticket-dialog-text"
        )
    );

    if (typeof dialog.showModal === "function") {
        dialog.showModal();
    } else {
        dialog.setAttribute("open", "");
    }

    return true;
}


// Build the dropdown used to change a ticket's status.
function createStatusSelect(ticket) {
    const currentStatus = TICKET_STATUSES.includes(ticket.status)
        ? ticket.status
        : "Open";

    const select = document.createElement("select");

    select.className = `status-select ${statusClass(currentStatus)}`;
    select.setAttribute("aria-label", `Status for ${ticket.id}`);

    TICKET_STATUSES.forEach((status) => {
        const option = document.createElement("option");

        option.value = status;
        option.textContent = status;
        option.selected = status === currentStatus;

        select.appendChild(option);
    });

    select.addEventListener("change", () => {
        changeTicketStatus(ticket.id, select.value, select);
    });

    return select;
}


// Save a new status for a ticket, then refresh the dashboard.
async function changeTicketStatus(ticketId, status, select) {
    select.disabled = true;

    try {
        const response = await fetch(
            `/api/tickets/${encodeURIComponent(ticketId)}/status`,
            {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ status: status })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to update the ticket.");
        }

        printTerminalMessage(`Updated ${ticketId}: status is now ${status}.`);

        await loadTickets();

    } catch (error) {
        console.error("Status update failed:", error);

        printTerminalMessage(
            `Could not update ${ticketId}: ${error.message}`,
            "error"
        );

        await loadTickets();
    }
}


// Load saved tickets and update the dashboard.
async function loadTickets() {
    const tableBody = document.getElementById("ticket-table-body");

    if (!tableBody) {
        console.error("Ticket table body was not found.");
        return;
    }

    try {
        const response = await fetch("/api/tickets");

        if (!response.ok) {
            throw new Error("Unable to retrieve tickets.");
        }

        const data = await response.json();
        const tickets = data.tickets;

        if (!Array.isArray(tickets)) {
            throw new Error("Invalid ticket data received.");
        }

        loadedTickets = tickets;

        tableBody.replaceChildren();

        if (tickets.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");

            cell.colSpan = 4;
            cell.textContent = "No tickets found.";
            cell.className = "empty-state";

            row.appendChild(cell);
            tableBody.appendChild(row);
        } else {
            tickets.forEach((ticket) => {
                const row = document.createElement("tr");

                const idCell = document.createElement("td");
                idCell.textContent = ticket.id || "N/A";

                const titleCell = document.createElement("td");
                const titleButton = document.createElement("button");

                titleButton.type = "button";
                titleButton.className = "ticket-link";
                titleButton.textContent = ticket.title || "Untitled";
                titleButton.title = "View ticket details";
                titleButton.addEventListener("click", () => {
                    openTicketDialog(ticket.id);
                });

                titleCell.appendChild(titleButton);

                const providerCell = document.createElement("td");
                providerCell.textContent = ticket.ai_provider || "N/A";

                row.append(idCell, titleCell, providerCell);

                const statusCell = document.createElement("td");
                statusCell.appendChild(createStatusSelect(ticket));
                row.appendChild(statusCell);

                tableBody.appendChild(row);
            });
        }

        updateStatistics(tickets);

        const countLabel = document.getElementById("ticket-count-label");

        if (countLabel) {
            countLabel.textContent =
                `${tickets.length} saved ticket(s)`;
        }

    } catch (error) {
        console.error("Ticket loading failed:", error);

        tableBody.replaceChildren();

        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.textContent = "Unable to load tickets. Please refresh.";
        cell.className = "empty-state";

        row.appendChild(cell);
        tableBody.appendChild(row);

        const countLabel = document.getElementById("ticket-count-label");

        if (countLabel) {
            countLabel.textContent = "Unable to load saved requests.";
        }
    }
}


// Update dashboard statistics.
function updateStatistics(tickets) {
    const totalElement = document.getElementById("total-tickets");
    const aiElement = document.getElementById("ai-tickets");
    const openElement = document.getElementById("open-tickets");

    const total = tickets.length;

    const aiAssisted = tickets.filter((ticket) => {
        return Boolean(ticket.ai_provider && ticket.ai_suggestions);
    }).length;

    const openTickets = tickets.filter((ticket) => {
        return (ticket.status || "open").toLowerCase() !== "resolved";
    }).length;

    if (totalElement) {
        totalElement.textContent = total;
    }

    if (aiElement) {
        aiElement.textContent = aiAssisted;
    }

    if (openElement) {
        openElement.textContent = openTickets;
    }
}


// Display a message in the dashboard terminal.
function printTerminalMessage(message, type = "output") {
    const terminal = document.getElementById("terminal-output");

    if (!terminal) {
        console.error("Terminal output element was not found.");
        return;
    }

    const line = document.createElement("div");

    line.className = `terminal-line ${type}`;
    line.textContent = message;

    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}


// Handle commands entered into the dashboard terminal.
async function handleCommand(command) {
    const normalizedCommand = command.trim().toLowerCase();

    if (!normalizedCommand) {
        return;
    }

    printTerminalMessage(`> ${command}`, "command");

    if (normalizedCommand.startsWith("view ")) {
        const ticketId = normalizedCommand.slice(5).trim().toUpperCase();

        if (!openTicketDialog(ticketId)) {
            printTerminalMessage(`Ticket ${ticketId} was not found.`, "error");
        }

        return;
    }

    switch (normalizedCommand) {
        case "help":
            printTerminalMessage("Available commands: help, list, view, refresh, clear");
            printTerminalMessage("help    - Show available commands.");
            printTerminalMessage("list    - Display saved tickets.");
            printTerminalMessage("view ID - Open a ticket, e.g. view T001.");
            printTerminalMessage("refresh - Reload tickets and provider status.");
            printTerminalMessage("clear   - Clear terminal output.");
            break;

        case "list":
            try {
                const response = await fetch("/api/tickets");

                if (!response.ok) {
                    throw new Error("Ticket request failed.");
                }

                const data = await response.json();
                const tickets = data.tickets || [];

                if (tickets.length === 0) {
                    printTerminalMessage("No saved tickets found.");
                    break;
                }

                printTerminalMessage(
                    `Found ${tickets.length} saved ticket(s):`
                );

                tickets.forEach((ticket) => {
                    printTerminalMessage(
                        `${ticket.id || "N/A"} | ` +
                        `${ticket.title || "Untitled"} | ` +
                        `Provider: ${ticket.ai_provider || "N/A"} | ` +
                        `Status: ${ticket.status || "Open"}`
                    );
                });

            } catch (error) {
                console.error("Unable to list tickets:", error);

                printTerminalMessage(
                    "Unable to retrieve tickets. Please try again.",
                    "error"
                );
            }
            break;

        case "refresh":
            await loadTickets();
            await loadProviderStatus();
            printTerminalMessage("Dashboard refreshed.");
            break;

        case "clear": {
            const terminal = document.getElementById("terminal-output");

            if (terminal) {
                terminal.replaceChildren();
            }
            break;
        }

        default:
            printTerminalMessage(
                `Unknown command: ${command}. Type help to see available commands.`,
                "error"
            );
    }
}


// Submit a ticket to the selected AI provider.
async function diagnoseTicket(event) {
    event.preventDefault();

    const form = document.getElementById("ticket-form");
    const titleInput = document.getElementById("ticket-title");
    const descriptionInput = document.getElementById("ticket-description");
    const providerInput = document.getElementById("ai-provider");

    const button = document.getElementById("diagnose-button");
    const message = document.getElementById("diagnosis-message");
    const results = document.getElementById("diagnosis-results");
    const suggestionsOutput = document.getElementById("diagnosis-suggestions");

    if (
        !form ||
        !titleInput ||
        !descriptionInput ||
        !providerInput ||
        !button ||
        !message ||
        !results ||
        !suggestionsOutput
    ) {
        console.error("One or more ticket form elements are missing.");
        return;
    }

    const title = titleInput.value.trim();
    const description = descriptionInput.value.trim();
    const provider = providerInput.value.trim().toLowerCase();

    const validProviders = ["gemini", "groq", "openrouter"];

    if (!title || !description) {
        message.textContent = "Enter a ticket title and description.";
        results.hidden = true;
        return;
    }

    if (!validProviders.includes(provider)) {
        message.textContent = "Please select a valid AI provider.";
        results.hidden = true;
        console.error("Invalid AI provider:", provider);
        return;
    }

    console.log("Selected AI provider:", provider);

    button.disabled = true;
    button.textContent = "Diagnosing...";
    message.textContent = `Sending ticket to ${provider}...`;
    results.hidden = true;
    suggestionsOutput.textContent = "";

    try {
        const response = await fetch("/api/diagnose", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: title,
                description: description,
                provider: provider
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || `The ${provider} request failed.`
            );
        }

        message.textContent =
            `${data.message || "Diagnosis successful."} ` +
            `Ticket ID: ${data.ticket.id}`;

        suggestionsOutput.textContent = data.suggestions;
        results.hidden = false;

        await loadTickets();
        await loadProviderStatus();

        printTerminalMessage(
            `Created ${data.ticket.id}: ${data.ticket.title} ` +
            `using ${provider}.`
        );

        form.reset();

    } catch (error) {
        console.error(`${provider} diagnosis failed:`, error);

        message.textContent =
            error.message || "Diagnosis failed. Please try again.";

    } finally {
        button.disabled = false;
        button.textContent = "✳ Diagnose with AI";
    }
}


// Connect dashboard controls when the page loads.
document.addEventListener("DOMContentLoaded", () => {
    loadTickets();
    loadProviderStatus();

    const refreshButton = document.getElementById("refresh-tickets");

    if (refreshButton) {
        refreshButton.addEventListener("click", async () => {
            await loadTickets();
            await loadProviderStatus();
        });
    }

    const commandForm = document.getElementById("command-form");
    const commandInput = document.getElementById("command-input");

    if (commandForm && commandInput) {
        commandForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const command = commandInput.value;
            commandInput.value = "";

            await handleCommand(command);
            commandInput.focus();
        });
    }

    const ticketForm = document.getElementById("ticket-form");

    if (ticketForm) {
        ticketForm.addEventListener("submit", diagnoseTicket);
    }
});