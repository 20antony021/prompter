import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

const sql = postgres(process.env.POSTGRES_URL!, {
  max: 20,
  idle_timeout: 20,
  connect_timeout: 10,
  max_lifetime: 60 * 30,
  prepare: false,
});

export const db = drizzle(sql, {
  schema,
});
