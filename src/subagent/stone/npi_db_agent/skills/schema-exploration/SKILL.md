---
name: schema-exploration
description: 列出表、描述列与数据类型、识别外键与实体关系。当用户询问数据库结构、表有哪些、字段含义、外键或表之间如何关联时使用。
---

# 结构探索技能

> 本文件是 **Skill 工作流**，不是数据库表。业务数据在 `data/demo.db`（9 张表）。

## 工作流程

### 1. 列出所有表

使用 `sql_db_list_tables`。当前业务库应包含：

`categories`, `suppliers`, `products`, `product_suppliers`, `customers`, `orders`, `order_items`, `payments`, `inventory_movements`

若与上述不一致，**以工具返回为准**。

### 2. 获取指定表的结构

使用 `sql_db_schema` 查看列名、类型、示例行、主键与外键。

### 3. 映射关系（核心外键）

- `products.category_id` → `categories.id`
- `product_suppliers` → `products` / `suppliers`
- `orders.customer_id` → `customers.id`
- `order_items.order_id` → `orders.id`
- `order_items.product_id` → `products.id`
- `payments.order_id` → `orders.id`
- `inventory_movements.product_id` → `products.id`

### 4. 回答问题

说明表用途、列含义、JOIN 路径。提醒用户：订单金额在 `order_items.line_amount`，不在旧的 `orders.total_amount`。

## 示例："有哪些表？"

`sql_db_list_tables` → 按业务域分组说明（分类/商品/客户/订单/支付/库存）。

## 示例："orders 和 order_items 区别？"

- `orders`：订单头（客户、日期、状态、收货城市）
- `order_items`：每行商品、数量、单价、行金额

## 质量准则

- 列全表名与简要说明
- 说明主键、外键
- 区分 demo.db 与 chat.db、区分 skill 文档与 SQL 表
