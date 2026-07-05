import { HttpResponse } from "msw";
import { db } from "./db";
import type { User } from "../types";

export function tokenFor(user: User): string {
  return `token-${user.id}`;
}

export function userFromRequest(request: Request): User | null {
  const authHeader = request.headers.get("Authorization") ?? "";
  const token = authHeader.replace(/^Bearer\s+/i, "");
  const user = db.users.find((u) => tokenFor(u) === token);
  return user ?? null;
}

export function unauthorized() {
  return HttpResponse.json(
    { error: { code: "unauthorized", message: "請先登入" } },
    { status: 401 },
  );
}
