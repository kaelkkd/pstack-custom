import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Type } from "typebox";

const here = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(here, "..");
const profiles = new Set(["generalPurpose", "poteto-agent", "comment-sicko"]);
const taskSchema = Type.Object({
  agent: Type.String({ description: "generalPurpose, poteto-agent, or comment-sicko" }),
  task: Type.String({ minLength: 1 }),
  readonly: Type.Optional(Type.Boolean()),
});

async function runOne(item, ctx, signal) {
  if (!profiles.has(item.agent)) throw new Error(`Unknown pstack agent: ${item.agent}`);
  const readonly = item.readonly === true || item.agent === "comment-sicko";
  const adapter = await readFile(join(packageRoot, "docs", "adapter.md"), "utf8");
  const profile = item.agent === "generalPurpose"
    ? "Use the active Pi model and the current project instructions."
    : await readFile(join(packageRoot, "agents", `${item.agent}.md`), "utf8");
  const prompt = [
    "You are an isolated Pi subagent delegated by a parent chat.",
    `Your profile is ${item.agent}.`,
    "The following Pi adapter overrides conflicting Cursor-specific text in the profile and skills:",
    adapter,
    "Agent profile:",
    profile,
    `The poteto-mode skill is at ${join(packageRoot, "skills", "poteto-mode", "SKILL.md")}.`,
    readonly ? "Read-only assignment: do not edit files or run commands that change files." : "",
    "Delegated task:",
    item.task,
  ].filter(Boolean).join("\n\n");
  const temp = await mkdtemp(join(tmpdir(), "pstack-pi-"));
  try {
    const promptFile = join(temp, "task.md");
    await writeFile(promptFile, prompt, "utf8");
    const cliScript = process.argv[1]?.endsWith(".js") ? process.argv[1] : null;
    const args = [...(cliScript ? [cliScript] : []), "--print", "--no-session", "--no-extensions", "--no-mcp"];
    if (ctx.model?.provider && ctx.model?.id) {
      args.push("--model", `${ctx.model.provider}/${ctx.model.id}`);
    }
    if (ctx.thinkingLevel) args.push("--thinking", ctx.thinkingLevel);
    if (readonly) args.push("--tools", "read,grep,find,ls");
    args.push(`@${promptFile}`, "Complete the delegated task in the attached file.");
    return await new Promise((fulfill, reject) => {
      const child = spawn(process.execPath, args, {
        cwd: ctx.cwd,
        shell: false,
        windowsHide: true,
        stdio: ["ignore", "pipe", "pipe"],
      });
      let output = "";
      let errors = "";
      const cap = (current, chunk, limit) => (current + chunk.toString("utf8")).slice(-limit);
      child.stdout.on("data", chunk => { output = cap(output, chunk, 65536); });
      child.stderr.on("data", chunk => { errors = cap(errors, chunk, 16384); });
      const abort = () => child.kill();
      if (signal?.aborted) abort();
      else signal?.addEventListener("abort", abort, { once: true });
      child.on("error", reject);
      child.on("close", code => {
        signal?.removeEventListener("abort", abort);
        if (signal?.aborted) reject(new Error("Delegation aborted"));
        else if (code !== 0) reject(new Error(`Pi subagent exited ${code}: ${errors || output}`));
        else fulfill(output.trim());
      });
    });
  } finally {
    await rm(temp, { recursive: true, force: true });
  }
}

export default function (pi) {
  pi.registerTool({
    name: "pstack_task",
    label: "pstack task",
    description: "Delegate one or up to four independent tasks to isolated Pi subagents using the active model.",
    parameters: Type.Object({
      agent: Type.Optional(taskSchema.properties.agent),
      task: Type.Optional(taskSchema.properties.task),
      readonly: Type.Optional(Type.Boolean()),
      tasks: Type.Optional(Type.Array(taskSchema, { minItems: 1, maxItems: 4 })),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, ctx) {
      const items = params.tasks ?? (params.agent && params.task
        ? [{ agent: params.agent, task: params.task, readonly: params.readonly }]
        : null);
      if (!items) throw new Error("Provide agent and task, or tasks");
      const results = await Promise.allSettled(items.map(item => runOne(item, ctx, signal)));
      const text = results.map((result, index) => result.status === "fulfilled"
        ? `## ${items[index].agent}\n${result.value}`
        : `## ${items[index].agent}\nFailed: ${String(result.reason)}`
      ).join("\n\n");
      return { content: [{ type: "text", text }], details: { failures: results.filter(r => r.status === "rejected").length } };
    },
  });
}
