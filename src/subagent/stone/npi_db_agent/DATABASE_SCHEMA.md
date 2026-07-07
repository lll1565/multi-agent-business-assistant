# demo.db 业务库结构（权威参考）

> **重要**：`skills/` 目录下的 SKILL.md 是 Agent **工作流技能**，不是数据库表。  
> 真实表以 `sql_db_list_tables` / `sql_db_schema` 工具查询结果为准。

## 与 chat.db 的区别

| 文件 | 用途 | 表 |
|------|------|-----|
| `data/demo.db` | 电商业务只读查询 | 见下文 9 张表 |
| `data/chat.db` | Web 聊天会话 | sessions, messages |

## 实体关系（简图）

```
categories ──< products >── product_suppliers >── suppliers
                    │
                    ├──< order_items >── orders >── customers
                    │                      │
                    │                      └──< payments
                    └──< inventory_movements
```

## 表说明

### categories
商品分类。`id`, `name`, `description`

### suppliers
供应商。`id`, `name`, `contact_name`, `phone`, `city`

### products
商品 SKU。`id`, `sku`, `name`, `category_id` → categories, `unit_price`, `stock_qty`, `status`

### product_suppliers
商品-供应商多对多。`product_id`, `supplier_id`, `supply_price`, `is_primary`

### customers
客户。`id`, `name`, `email`, `city`, `tier` (standard/silver/gold), `join_date`

### orders
订单头（不含商品明细）。`id`, `customer_id`, `order_date`, `status`, `shipping_city`, `note`  
状态示例：pending / shipped / completed / cancelled

### order_items
订单行。`id`, `order_id`, `product_id`, `quantity`, `unit_price`, `line_amount`  
金额统计应 SUM(line_amount)，不要假设 orders 表有 total_amount 列。

### payments
支付记录。`id`, `order_id`, `pay_method`, `amount`, `paid_at`, `status`  
状态：paid / refunded / pending

### inventory_movements
库存流水。`id`, `product_id`, `delta_qty`（正入库负出库）, `reason`, `ref_order_id`, `created_at`

## 常用 JOIN 路径

- 订单金额：`order_items` JOIN `orders` ON order_id
- 客户城市：`orders` JOIN `customers` ON customer_id
- 商品分类：`products` JOIN `categories` ON category_id
- 供应商采购价：`products` JOIN `product_suppliers` JOIN `suppliers`
- 订单已付：`orders` JOIN `payments` ON order_id

## 已废弃（旧版 demo.db）

旧 schema 在 `orders` 表直接放 `product_id` / `total_amount`，**已拆分为 orders + order_items**。  
若工具返回的列与本文不一致，以 `sql_db_schema` 为准并更新查询。
