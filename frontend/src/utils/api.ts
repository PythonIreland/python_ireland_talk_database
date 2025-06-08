import { BACKEND_URL } from "../config";
export interface ExplorerItem {
  id: string;
  date: string;
  platform: string;
  title: string;
  description: string;
  tags: string[];
  source_url?: string;
  speakers?: string[];
}

interface FetchOpts {
  from?: Date | null;
  to?: Date | null;
  search?: string;
}

export async function fetchExplorerItems(
  opts: FetchOpts
): Promise<ExplorerItem[]> {
  const params = new URLSearchParams();
  if (opts.from) params.set("from", opts.from.toISOString());
  if (opts.to) params.set("to", opts.to.toISOString());
  if (opts.search) params.set("search", opts.search);
  const res = await fetch(`${BACKEND_URL}/explorer?${params}`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function fetchTags(): Promise<string[]> {
  const res = await fetch(`${BACKEND_URL}/tags`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}

export async function updateItemTags(
  id: string,
  tags: string[]
): Promise<void> {
  const res = await fetch(`${BACKEND_URL}/explorer/${id}/tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tags }),
  });
  if (!res.ok) throw new Error(res.statusText);
}

export async function fetchItemDetail(id: string): Promise<ExplorerItem> {
  const res = await fetch(`${BACKEND_URL}/explorer/${id}`);
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
}
