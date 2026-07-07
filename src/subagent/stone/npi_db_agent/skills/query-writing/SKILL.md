---
name: query-writing
description: 编写并执行从简单 SELECT 到复杂多表 JOIN、聚合和子查询的 SQL 查询。当用户要求查询数据库、编写 SQL、运行 SELECT 语句、检索数据、筛选记录或从数据库表生成报表时使用。
---

# 查询编写技能

> Skill 文档 ≠ 数据库表。写 SQL 前务必 `sql_db_schema` 确认列名。

## 简单查询

1. 确定表（如 `products`, `customers`）
2. `sql_db_schema` 查看列
3. SELECT 相关列 + WHERE + ORDER BY + **LIMIT 5**
4. `sql_db_query` 执行

## 复杂查询

### 1. 规划（`write_todos`）

- 订单销售额 → `order_items` + `orders` + 可选 `customers`
- 分类销量 → `order_items` + `products` + `categories`
- 供应商成本 → `product_suppliers` + `suppliers` + `products`
- 支付状态 → `payments` + `orders`

### 2. 检查结构

对每个涉及的表执行 `sql_db_schema`。

### 3. 构建查询

- 金额：`SUM(oi.line_amount)`，不要引用已废弃的 `orders.total_amount`
- JOIN 写在 FK = PK 上，使用表别名
- GROUP BY 包含所有非聚合列
- 默认 `LIMIT 5`

## 示例：按城市统计销售额

```sql
SELECT
    c.city,
    ROUND(SUM(oi.line_amount), 2) AS total_sales
FROM order_items oi
INNER JOIN orders o ON oi.order_id = o.id
INNER JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'completed'
GROUP BY c.city
ORDER BY total_sales DESC
LIMIT 5;
```

## 示例：库存低于 50 的商品及分类

```sql
SELECT
    p.sku,
    p.name,
    cat.name AS category,
    p.stock_qty
FROM products p
INNER JOIN categories cat ON p.category_id = cat.id
WHERE p.stock_qty < 50 AND p.status = 'active'
ORDER BY p.stock_qty ASC
LIMIT 5;
```

## 错误恢复

1. **列不存在** — 可能用了旧 schema（如 orders.product_id），改查 `order_items`
2. **空结果** — 检查 status / tier / 日期过滤
3. **结果过大** — 加强 WHERE 或 LIMIT

## 质量准则

- 只读 SELECT
- 避免 `SELECT *`
- 多表问题先 list_tables + schema
