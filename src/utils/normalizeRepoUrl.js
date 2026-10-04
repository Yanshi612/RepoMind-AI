export function normalizeRepoUrl(value) {
  if (typeof value === "string") return value;

  if (value && typeof value === "object") {
    for (const key of ["url", "html_url", "repo_url"]) {
      if (typeof value[key] === "string") {
        return value[key];
      }
    }
  }

  return "";
}
