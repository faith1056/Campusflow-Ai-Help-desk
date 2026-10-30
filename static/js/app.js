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

                const values = [
                    ticket.id || "N/A",
                    ticket.title || "Untitled",
                    ticket.ai_provider || "N/A",
                    ticket.status || "Open"
                ];

                values.forEach((value) => {
                    const cell = document.createElement("td");
                    cell.textContent = value;
                    row.appendChild(cell);
                });

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

    switch (normalizedCommand) {
        case "help":
            printTerminalMessage("Available commands: help, list, refresh, clear");
            printTerminalMessage("help    - Show available commands.");
            printTerminalMessage("list    - Display saved tickets.");
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
                        `Provider: ${ticket.ai_provider || "N/A"}`
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
