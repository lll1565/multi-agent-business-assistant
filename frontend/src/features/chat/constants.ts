export const STORAGE_KEY = "multi_agent_current_session";

export const CHAT_EXAMPLES: string[] = [
  "数据库里有哪些表？",
  "列出前 5 条订单记录",
  "查看 get_users 接口文档",
];

export type ChatExample = (typeof CHAT_EXAMPLES)[number];
