import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  videos: defineTable({
    url: v.string(), // YouTube URL
    title: v.optional(v.string()),
    duration: v.optional(v.number()),
    status: v.string(), // "analyzing", "waiting_for_selection", "processing", "completed", "failed"
    createdAt: v.number(),
    callbackUrl: v.optional(v.string()), // Webhook URL
  }),
  clips: defineTable({
    videoId: v.id("videos"),
    start: v.number(),
    end: v.number(),
    score: v.number(),
    reasoning: v.string(),
    status: v.string(), // "pending", "processing", "done", "failed"
    output_path: v.optional(v.string()), // Local path for now
    selected: v.boolean(),
  }),
});
