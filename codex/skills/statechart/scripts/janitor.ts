import fs from "node:fs";
import { killGroup } from "./run.ts";

const [pid, stage, temporary] = process.argv.slice(2);
process.stdin.once("end", async () => {
  await killGroup(Number(pid));
  for (const directory of [stage, temporary]) {
    try {
      fs.rmSync(directory, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 });
    } catch {
      // The parent also cleans these folders after a normal exit.
    }
  }
});
process.stdin.resume();
