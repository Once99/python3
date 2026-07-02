import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const FIGMA_API_BASE = "https://api.figma.com/v1";
const MAX_RESPONSE_CHARS = Number.parseInt(
  process.env.FIGMA_MCP_MAX_RESPONSE_CHARS ?? "60000",
  10
);

const token = process.env.FIGMA_ACCESS_TOKEN;

if (!token) {
  console.error(
    "Missing FIGMA_ACCESS_TOKEN. Set it in your MCP client env or shell before starting the server."
  );
}

const server = new McpServer({
  name: "local-figma-mcp",
  version: "1.0.0",
});

type FigmaApiOptions = {
  query?: Record<string, string | undefined>;
};

async function figmaGet(pathname: string, options: FigmaApiOptions = {}) {
  if (!token) {
    throw new Error("FIGMA_ACCESS_TOKEN is not configured.");
  }

  const url = new URL(`${FIGMA_API_BASE}${pathname}`);

  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value) {
      url.searchParams.set(key, value);
    }
  }

  const response = await fetch(url, {
    headers: {
      "X-Figma-Token": token,
    },
  });

  const responseText = await response.text();

  if (!response.ok) {
    throw new Error(
      `Figma API ${response.status} ${response.statusText}: ${responseText}`
    );
  }

  return JSON.parse(responseText) as unknown;
}

function toTextContent(value: unknown, maxChars = MAX_RESPONSE_CHARS) {
  const text = JSON.stringify(value, null, 2);
  const truncated =
    text.length > maxChars
      ? `${text.slice(0, maxChars)}\n\n[Truncated at ${maxChars} characters. Use narrower ids/depth or raise FIGMA_MCP_MAX_RESPONSE_CHARS.]`
      : text;

  return {
    content: [
      {
        type: "text" as const,
        text: truncated,
      },
    ],
  };
}

const fileKeySchema = z
  .string()
  .min(1)
  .describe("Figma file key, usually found after /design/ or /file/ in the URL.");

const nodeIdsSchema = z
  .array(z.string().min(1))
  .min(1)
  .describe("Figma node ids, for example 1:2. URL node-id values may use 1-2.");

server.tool(
  "get_figma_file",
  {
    fileKey: fileKeySchema,
    depth: z
      .number()
      .int()
      .min(1)
      .max(4)
      .optional()
      .describe("Optional traversal depth. Keep this small for large files."),
    branchData: z.boolean().optional(),
  },
  async ({ fileKey, depth, branchData }) => {
    const data = await figmaGet(`/files/${encodeURIComponent(fileKey)}`, {
      query: {
        depth: depth?.toString(),
        branch_data: branchData ? "true" : undefined,
      },
    });

    return toTextContent(data);
  }
);

server.tool(
  "get_figma_nodes",
  {
    fileKey: fileKeySchema,
    nodeIds: nodeIdsSchema,
    depth: z.number().int().min(1).max(6).optional(),
  },
  async ({ fileKey, nodeIds, depth }) => {
    const normalizedNodeIds = nodeIds.map((nodeId) => nodeId.replace("-", ":"));
    const data = await figmaGet(`/files/${encodeURIComponent(fileKey)}/nodes`, {
      query: {
        ids: normalizedNodeIds.join(","),
        depth: depth?.toString(),
      },
    });

    return toTextContent(data);
  }
);

server.tool(
  "get_figma_images",
  {
    fileKey: fileKeySchema,
    nodeIds: nodeIdsSchema,
    format: z.enum(["jpg", "png", "svg", "pdf"]).default("png"),
    scale: z.number().min(0.01).max(4).default(1),
    svgOutlineText: z.boolean().default(true),
  },
  async ({ fileKey, nodeIds, format, scale, svgOutlineText }) => {
    const normalizedNodeIds = nodeIds.map((nodeId) => nodeId.replace("-", ":"));
    const data = await figmaGet(`/images/${encodeURIComponent(fileKey)}`, {
      query: {
        ids: normalizedNodeIds.join(","),
        format,
        scale: scale.toString(),
        svg_outline_text: svgOutlineText ? "true" : "false",
      },
    });

    return toTextContent(data);
  }
);

server.tool(
  "get_figma_components",
  {
    fileKey: fileKeySchema,
  },
  async ({ fileKey }) => {
    const data = await figmaGet(
      `/files/${encodeURIComponent(fileKey)}/components`
    );

    return toTextContent(data);
  }
);

server.tool(
  "get_figma_styles",
  {
    fileKey: fileKeySchema,
  },
  async ({ fileKey }) => {
    const data = await figmaGet(`/files/${encodeURIComponent(fileKey)}/styles`);

    return toTextContent(data);
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
