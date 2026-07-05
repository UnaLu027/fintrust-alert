import { http, HttpResponse, delay } from "msw";
import { db, nextId } from "../db";
import { tokenFor, unauthorized, userFromRequest } from "../authHelper";
import type { LoginPayload, RegisterPayload, User } from "../../types";

export const authHandlers = [
  http.post("/api/auth/register", async ({ request }) => {
    const body = (await request.json()) as RegisterPayload;
    await delay(300);

    if (db.users.some((u) => u.email === body.email)) {
      return HttpResponse.json(
        { error: { code: "email_taken", message: "此 Email 已被註冊" } },
        { status: 409 },
      );
    }

    const user: User = {
      id: nextId("user"),
      email: body.email,
      investmentExperience: body.investmentExperience,
      watchedMarkets: body.watchedMarkets,
      watchedCompanies: body.watchedCompanies,
      watchedIndustries: body.watchedIndustries,
      watchedKeywords: body.watchedKeywords,
      alertFrequency: body.alertFrequency,
      alertTypes: body.alertTypes,
      createdAt: new Date().toISOString(),
    };
    db.users.push(user);
    db.passwords.set(user.email, body.password);

    return HttpResponse.json({ token: tokenFor(user), user }, { status: 201 });
  }),

  http.post("/api/auth/login", async ({ request }) => {
    const body = (await request.json()) as LoginPayload;
    await delay(300);

    const user = db.users.find((u) => u.email === body.email);
    const storedPassword = user ? db.passwords.get(user.email) : undefined;

    if (!user || storedPassword !== body.password) {
      return HttpResponse.json(
        { error: { code: "invalid_credentials", message: "帳號或密碼錯誤" } },
        { status: 401 },
      );
    }

    return HttpResponse.json({ token: tokenFor(user), user });
  }),

  http.post("/api/auth/logout", async () => {
    await delay(100);
    return HttpResponse.json({ ok: true });
  }),

  http.get("/api/auth/me", async ({ request }) => {
    const user = userFromRequest(request);
    if (!user) return unauthorized();
    await delay(150);
    return HttpResponse.json({ user });
  }),
];
