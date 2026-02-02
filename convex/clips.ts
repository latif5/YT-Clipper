import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    videoId: v.id("videos"),
    start: v.number(),
    end: v.number(),
    score: v.number(),
    reasoning: v.string(),
    status: v.string(),
    selected: v.boolean(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("clips", args);
  },
});

export const listByVideo = query({
  args: { videoId: v.id("videos") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("clips")
      .filter((q) => q.eq(q.field("videoId"), args.videoId))
      .collect();
  },
});

export const get = query({
  args: { id: v.id("clips") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const select = mutation({
  args: { id: v.id("clips") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { selected: true });
  },
});

export const updateStatus = mutation({
  args: {
    id: v.id("clips"),
    status: v.string(),
    output_path: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    await ctx.db.patch(id, fields);
  },
});
