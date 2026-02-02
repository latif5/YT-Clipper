import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    url: v.string(),
    status: v.string(),
    callbackUrl: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("videos")
      .filter((q) => q.eq(q.field("url"), args.url))
      .first();
    
    if (existing) {
      if (args.callbackUrl && args.callbackUrl !== existing.callbackUrl) {
           await ctx.db.patch(existing._id, { callbackUrl: args.callbackUrl });
      }
      return existing._id;
    }

    return await ctx.db.insert("videos", {
      url: args.url,
      status: args.status,
      createdAt: Date.now(),
      callbackUrl: args.callbackUrl,
    });
  },
});

export const updateStatus = mutation({
  args: {
    id: v.id("videos"),
    status: v.string(),
    title: v.optional(v.string()),
    duration: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    await ctx.db.patch(id, fields);
  },
});

export const get = query({
  args: { id: v.id("videos") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});
