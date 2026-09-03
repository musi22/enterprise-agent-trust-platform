import asyncio
import random
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from apps.api.app.db.database import engine, AsyncSessionLocal, Base
from apps.api.app.db.models import (
    User, Product, Inventory, Cart, CartItem, Order, OrderItem, RefundRequest,
    IdempotencyKey, Scenario, EvidenceReceipt, AgentEvent, ToolCall, AgentRun, PolicyDecision, Approval
)
from apps.api.app.core.security import get_password_hash

# 52 Products across 6 categories
PRODUCTS_SEED_DATA = [
    # Electronics
    {"id": "prod_elec_001", "sku": "ELEC-HEADPH-001", "title": "AcousticMax Pro Noise-Cancelling Headphones", "category": "Electronics", "price_cents": 19999, "stock_level": 45, "description": "Over-ear active noise cancelling headphones with 40-hour battery life."},
    {"id": "prod_elec_002", "sku": "ELEC-CHARGER-002", "title": "VoltFast 65W GaN Fast Charger USB-C", "category": "Electronics", "price_cents": 3499, "stock_level": 120, "description": "Dual-port compact GaN charger compatible with laptops and smartphones."},
    {"id": "prod_elec_003", "sku": "ELEC-KEYBOARD-003", "title": "MechTypist RGB Mechanical Keyboard", "category": "Electronics", "price_cents": 8999, "stock_level": 30, "description": "Tactile brown switches with customizable per-key backlighting and wrist rest."},
    {"id": "prod_elec_004", "sku": "ELEC-MOUSE-004", "title": "ErgoPrecision Wireless Mouse", "category": "Electronics", "price_cents": 4999, "stock_level": 75, "description": "Ergonomic vertical wireless mouse with silent click buttons."},
    {"id": "prod_elec_005", "sku": "ELEC-WEBCAM-005", "title": "StreamClear 4K Ultra HD Webcam", "category": "Electronics", "price_cents": 12999, "stock_level": 25, "description": "4K webcam with dual omnidirectional microphones and privacy cover."},
    {"id": "prod_elec_006", "sku": "ELEC-SPEAKER-006", "title": "SoundPebble Waterproof Bluetooth Speaker", "category": "Electronics", "price_cents": 5999, "stock_level": 60, "description": "IPX7 waterproof portable speaker with rich bass and 15-hour playback."},
    {"id": "prod_elec_007", "sku": "ELEC-MONITOR-007", "title": "VisionPro 27-inch QHD IPS Monitor", "category": "Electronics", "price_cents": 27999, "stock_level": 18, "description": "165Hz gaming and productivity display with HDR400 support."},
    {"id": "prod_elec_008", "sku": "ELEC-CABLE-008", "title": "Braided Thunderbolt 4 Cable 2M", "category": "Electronics", "price_cents": 2999, "stock_level": 150, "description": "40Gbps data transfer and 100W power delivery braided cable."},
    {"id": "prod_elec_009", "sku": "ELEC-SMARTWATCH-009", "title": "PulseFit Active Smartwatch", "category": "Electronics", "price_cents": 14999, "stock_level": 40, "description": "Fitness smartwatch with GPS, heart rate monitor, and 7-day battery life."},
    {"id": "prod_elec_010", "sku": "ELEC-TABLET-010", "title": "OmniTab 10.5-inch Digital Slate", "category": "Electronics", "price_cents": 34999, "stock_level": 0, "description": "Lightweight tablet for drawing and media consumption. (OUT OF STOCK)"},
    
    # Home & Kitchen
    {"id": "prod_home_011", "sku": "HOME-COFFEEMAK-011", "title": "AromaBrew 12-Cup Programmable Coffee Maker", "category": "Home & Kitchen", "price_cents": 7999, "stock_level": 35, "description": "Thermal carafe coffee maker with precision temperature control."},
    {"id": "prod_home_012", "sku": "HOME-AIRFRYER-012", "title": "CrispWave 6-Quart Digital Air Fryer", "category": "Home & Kitchen", "price_cents": 11999, "stock_level": 22, "description": "Rapid air circulation air fryer with 8 one-touch cooking presets."},
    {"id": "prod_home_013", "sku": "HOME-BLENDER-013", "title": "NutriVortex High-Speed Blender 1200W", "category": "Home & Kitchen", "price_cents": 9999, "stock_level": 50, "description": "Heavy duty kitchen blender for smoothies, soups, and crushing ice."},
    {"id": "prod_home_014", "sku": "HOME-KETTLE-014", "title": "PureBoil Gooseneck Electric Kettle", "category": "Home & Kitchen", "price_cents": 4599, "stock_level": 65, "description": "Variable temperature pour-over kettle with stainless steel interior."},
    {"id": "prod_home_015", "sku": "HOME-ROBOTVAC-015", "title": "CleanBot Smart LiDAR Robot Vacuum", "category": "Home & Kitchen", "price_cents": 39999, "stock_level": 12, "description": "Laser navigation robot vacuum and mop with auto-empty station."},
    {"id": "prod_home_016", "sku": "HOME-KNIFESET-016", "title": "MasterChef 8-Piece Japanese Steel Knife Block", "category": "Home & Kitchen", "price_cents": 15999, "stock_level": 28, "description": "High-carbon stainless steel knife set with ergonomic Pakkawood handles."},
    {"id": "prod_home_017", "sku": "HOME-PAN-017", "title": "GraniteStone Non-Stick 10-Inch Frying Pan", "category": "Home & Kitchen", "price_cents": 3299, "stock_level": 80, "description": "PTFE and PFOA free mineral-infused non-stick cooking pan."},
    {"id": "prod_home_018", "sku": "HOME-AIRPUR-018", "title": "BreathePure True HEPA Air Purifier", "category": "Home & Kitchen", "price_cents": 13999, "stock_level": 34, "description": "3-stage filtration capturing 99.97% of airborne allergens and dust."},
    {"id": "prod_home_019", "sku": "HOME-DIFFUSER-019", "title": "ZenMist Ultrasonic Aromatherapy Diffuser", "category": "Home & Kitchen", "price_cents": 2499, "stock_level": 90, "description": "Quiet essential oil diffuser with ambient 7-color LED lighting."},
    {"id": "prod_home_020", "sku": "HOME-TOASTER-020", "title": "RetroStyle 4-Slice Stainless Toaster", "category": "Home & Kitchen", "price_cents": 5499, "stock_level": 0, "description": "Classic vintage 4-slot toaster with bagel and defrost settings. (OUT OF STOCK)"},

    # Apparel & Footwear
    {"id": "prod_app_021", "sku": "APP-HOODIE-021", "title": "CloudSoft Heavyweight Fleece Hoodie (Black)", "category": "Apparel", "price_cents": 6499, "stock_level": 110, "description": "Organic cotton relaxed fit pullover hoodie with brushed interior."},
    {"id": "prod_app_022", "sku": "APP-JACKET-022", "title": "StormShield Waterproof Mountain Parka", "category": "Apparel", "price_cents": 18999, "stock_level": 25, "description": "Breathable 3-layer weatherproof hooded shell jacket."},
    {"id": "prod_app_023", "sku": "APP-RUNSHOES-023", "title": "AeroStride Carbon-Plate Running Shoes", "category": "Apparel", "price_cents": 15999, "stock_level": 42, "description": "Lightweight marathon racing shoes with energy-returning foam."},
    {"id": "prod_app_024", "sku": "APP-SOCKS-024", "title": "Merino Wool Thermal Hiking Socks 3-Pack", "category": "Apparel", "price_cents": 2499, "stock_level": 200, "description": "Moisture-wicking, anti-odor cushioned merino wool crew socks."},
    {"id": "prod_app_025", "sku": "APP-TEE-025", "title": "Essential Supima Cotton T-Shirt", "category": "Apparel", "price_cents": 2299, "stock_level": 140, "description": "Classic crewneck tee crafted from 100% American-grown Supima cotton."},
    {"id": "prod_app_026", "sku": "APP-JEANS-026", "title": "FlexComfort Slim-Fit Denim Jeans", "category": "Apparel", "price_cents": 7499, "stock_level": 55, "description": "Stretch denim jeans with comfortable all-day movement and durable rivets."},
    {"id": "prod_app_027", "sku": "APP-SUNGLASS-027", "title": "Horizon Polarized Aviator Sunglasses", "category": "Apparel", "price_cents": 6999, "stock_level": 85, "description": "Classic lightweight titanium frame with UV400 polarized lenses."},
    {"id": "prod_app_028", "sku": "APP-BEANIE-028", "title": "Alpine Ribbed Knit Cashmere Beanie", "category": "Apparel", "price_cents": 3999, "stock_level": 70, "description": "100% Mongolian cashmere warm winter ribbed watch cap."},
    {"id": "prod_app_029", "sku": "APP-GLOVES-029", "title": "TouchGrip Leather Winter Gloves", "category": "Apparel", "price_cents": 4999, "stock_level": 48, "description": "Genuine lambskin leather gloves with full touchscreen compatibility."},
    {"id": "prod_app_030", "sku": "APP-BELT-030", "title": "Full-Grain Italian Leather Dress Belt", "category": "Apparel", "price_cents": 3899, "stock_level": 60, "description": "Handcrafted durable leather belt with brushed silver buckle."},

    # Books & Stationery
    {"id": "prod_book_031", "sku": "BOOK-DDIA-031", "title": "Designing Data-Intensive Applications", "category": "Books", "price_cents": 4999, "stock_level": 85, "description": "The big ideas behind reliable, scalable, and maintainable systems by Martin Kleppmann."},
    {"id": "prod_book_032", "sku": "BOOK-SRE-032", "title": "Site Reliability Engineering: How Google Runs Production Systems", "category": "Books", "price_cents": 4499, "stock_level": 60, "description": "Practical insights and culture behind Google's production systems."},
    {"id": "prod_book_033", "sku": "BOOK-SYSTEM-033", "title": "System Design Interview – An Insider's Guide", "category": "Books", "price_cents": 3999, "stock_level": 115, "description": "Step-by-step system design architectural frameworks by Alex Xu."},
    {"id": "prod_book_034", "sku": "BOOK-CLEAN-034", "title": "Clean Code: A Handbook of Agile Software Craftsmanship", "category": "Books", "price_cents": 4299, "stock_level": 95, "description": "Core software engineering principles, patterns, and refactoring practices."},
    {"id": "prod_book_035", "sku": "BOOK-NOTEBOOK-035", "title": "GridCraft Dot Matrix Hardcover Notebook", "category": "Stationery", "price_cents": 1999, "stock_level": 130, "description": "160gsm bleed-proof dotted journal with expandable back pocket."},
    {"id": "prod_book_036", "sku": "BOOK-PEN-036", "title": "AeroFlow Precision Rollerball Pens 6-Pack", "category": "Stationery", "price_cents": 1499, "stock_level": 210, "description": "0.5mm extra-fine quick-drying waterproof black ink pens."},
    {"id": "prod_book_037", "sku": "BOOK-DESKPAD-037", "title": "Dual-Sided Eco-Leather Desk Pad 90x45cm", "category": "Stationery", "price_cents": 2699, "stock_level": 75, "description": "Waterproof PU leather desk blotter and extended gaming mouse mat."},
    {"id": "prod_book_038", "sku": "BOOK-ORGANIZER-038", "title": "Solid Bamboo Desktop Cable & Pen Organizer", "category": "Stationery", "price_cents": 2999, "stock_level": 40, "description": "Natural bamboo desktop tidy organizer with multiple compartments."},

    # Health & Personal Care
    {"id": "prod_hlth_039", "sku": "HLTH-TOOTHBRUSH-039", "title": "SonicVibe Pro Electric Sonic Toothbrush", "category": "Health & Personal Care", "price_cents": 6999, "stock_level": 90, "description": "40,000 vibrations/min with smart 2-minute timer and travel case."},
    {"id": "prod_hlth_040", "sku": "HLTH-MASSAGER-040", "title": "TheraDeep Mini Percussive Massage Gun", "category": "Health & Personal Care", "price_cents": 8999, "stock_level": 45, "description": "Ultra-quiet portable deep tissue muscle massage device."},
    {"id": "prod_hlth_041", "sku": "HLTH-SCALE-041", "title": "SmartScale Bio-Impedance Body Composition Scale", "category": "Health & Personal Care", "price_cents": 3999, "stock_level": 70, "description": "Syncs weight, BMI, body fat %, and muscle mass with smartphone apps."},
    {"id": "prod_hlth_042", "sku": "HLTH-SUNSCREEN-042", "title": "HydraShield SPF 50 Mineral Sunscreen 100ml", "category": "Health & Personal Care", "price_cents": 1899, "stock_level": 160, "description": "Broad spectrum non-greasy zinc oxide mineral sunscreen."},
    {"id": "prod_hlth_043", "sku": "HLTH-SERUM-043", "title": "GlowMatrix Vitamin C + Hyaluronic Face Serum", "category": "Health & Personal Care", "price_cents": 2899, "stock_level": 85, "description": "Antioxidant brightening daily face serum for radiant skin."},
    {"id": "prod_hlth_044", "sku": "HLTH-PILLOW-044", "title": "ContourRest Ergonomic Cervical Memory Foam Pillow", "category": "Health & Personal Care", "price_cents": 4999, "stock_level": 55, "description": "Orthopedic neck support contour pillow for side and back sleepers."},

    # Sports & Outdoors
    {"id": "prod_sport_045", "sku": "SPRT-YOGAMAT-045", "title": "EcoGrip 6mm Non-Slip Natural Rubber Yoga Mat", "category": "Sports & Outdoors", "price_cents": 4599, "stock_level": 60, "description": "Extra dense alignment yoga mat with alignment guidelines."},
    {"id": "prod_sport_046", "sku": "SPRT-BOTTLE-046", "title": "HydroLock 32oz Insulated Stainless Steel Bottle", "category": "Sports & Outdoors", "price_cents": 2999, "stock_level": 140, "description": "Keeps beverages cold for 24 hours or hot for 12 hours with straw lid."},
    {"id": "prod_sport_047", "sku": "SPRT-BANDS-047", "title": "PowerFit Heavy-Duty Resistance Loop Bands Set", "category": "Sports & Outdoors", "price_cents": 1999, "stock_level": 180, "description": "5 color-coded resistance bands with door anchor and workout guide."},
    {"id": "prod_sport_048", "sku": "SPRT-TENT-048", "title": "RidgeLine 2-Person Ultralight Backpacking Tent", "category": "Sports & Outdoors", "price_cents": 21999, "stock_level": 15, "description": "Double-walled waterproof camping tent weighing under 3.5 lbs."},
    {"id": "prod_sport_049", "sku": "SPRT-BACKPACK-049", "title": "TrailExplorer 35L Daypack with Rain Cover", "category": "Sports & Outdoors", "price_cents": 7999, "stock_level": 40, "description": "Ergonomic hiking backpack with trekking pole attachments."},
    {"id": "prod_sport_050", "sku": "SPRT-HAMMOCK-050", "title": "DoubleNest Parachute Camping Hammock with Tree Straps", "category": "Sports & Outdoors", "price_cents": 3999, "stock_level": 95, "description": "Durable 210T nylon hammock supporting up to 500 lbs with carabiners."},
    {"id": "prod_sport_051", "sku": "SPRT-HEADLAMP-051", "title": "LumenPath 500-Lumen Rechargeable LED Headlamp", "category": "Sports & Outdoors", "price_cents": 2499, "stock_level": 110, "description": "Waterproof outdoor headlamp with red night vision and motion sensor."},
    {"id": "prod_sport_052", "sku": "SPRT-KAYAK-052", "title": "AquaGlide Inflatable Touring Kayak with Paddle", "category": "Sports & Outdoors", "price_cents": 29999, "stock_level": 8, "description": "Rigid drop-stitch floor inflatable single person recreational kayak."}
]

USERS_SEED_DATA = [
    # Customers
    {"id": "usr_cust_001", "name": "Alice Johnson", "email": "alice@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_002", "name": "Bob Smith", "email": "bob@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_003", "name": "Charlie Davis", "email": "charlie@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_004", "name": "David Martinez", "email": "david@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_005", "name": "Eve Wilson", "email": "eve@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_006", "name": "Frank Miller", "email": "frank@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_007", "name": "Grace Taylor", "email": "grace@customer.sandbox", "role": "customer", "password": "Password123!"},
    {"id": "usr_cust_008", "name": "Heidi Anderson", "email": "heidi@customer.sandbox", "role": "customer", "password": "Password123!"},
    
    # Support Agents
    {"id": "usr_agent_001", "name": "Sarah Support", "email": "sarah.support@retail.sandbox", "role": "support_agent", "password": "Password123!"},
    {"id": "usr_agent_002", "name": "Mike Support", "email": "mike.support@retail.sandbox", "role": "support_agent", "password": "Password123!"},
    
    # Administrators
    {"id": "usr_admin_001", "name": "Dave Admin", "email": "dave.admin@retail.sandbox", "role": "admin", "password": "AdminPassword123!"}
]

ORDERS_SEED_DATA = [
    {
        "id": "ord_1001",
        "user_id": "usr_cust_001",
        "order_status": "processing",
        "shipping_address": "742 Evergreen Terrace, Springfield, OR 97477",
        "total_cents": 19999,
        "idempotency_key": "idemp_seed_ord_1001",
        "items": [{"product_id": "prod_elec_001", "quantity": 1, "unit_price_cents": 19999}]
    },
    {
        "id": "ord_1002",
        "user_id": "usr_cust_001",
        "order_status": "shipped",
        "shipping_address": "742 Evergreen Terrace, Springfield, OR 97477",
        "total_cents": 3499,
        "idempotency_key": "idemp_seed_ord_1002",
        "items": [{"product_id": "prod_elec_002", "quantity": 1, "unit_price_cents": 3499}]
    },
    {
        "id": "ord_1003",
        "user_id": "usr_cust_002",
        "order_status": "delivered",
        "shipping_address": "221B Baker Street, Marylebone, London NW1 6XE",
        "total_cents": 12999,
        "idempotency_key": "idemp_seed_ord_1003",
        "items": [{"product_id": "prod_elec_005", "quantity": 1, "unit_price_cents": 12999}]
    },
    {
        "id": "ord_1004",
        "user_id": "usr_cust_002",
        "order_status": "cancelled",
        "shipping_address": "221B Baker Street, Marylebone, London NW1 6XE",
        "total_cents": 8999,
        "idempotency_key": "idemp_seed_ord_1004",
        "items": [{"product_id": "prod_elec_003", "quantity": 1, "unit_price_cents": 8999}]
    },
    {
        "id": "ord_1005",
        "user_id": "usr_cust_003",
        "order_status": "pending",
        "shipping_address": "12 Grimmauld Place, London N1",
        "total_cents": 4999,
        "idempotency_key": "idemp_seed_ord_1005",
        "items": [{"product_id": "prod_book_031", "quantity": 1, "unit_price_cents": 4999}]
    }
]

async def seed_database(session: AsyncSession, reset: bool = False) -> Dict[str, int]:
    """Deterministically seeds database with products, inventory, users, and orders."""
    if reset:
        # Clear tables in reverse dependency order
        for table in [
            EvidenceReceipt, AgentEvent, ToolCall, Approval, PolicyDecision, AgentRun,
            RefundRequest, OrderItem, Order, CartItem, Cart, Inventory, Product, User, IdempotencyKey
        ]:
            await session.execute(delete(table))
        await session.commit()

    # 1. Seed Users
    users_count = 0
    for u_data in USERS_SEED_DATA:
        existing = await session.execute(select(User).where(User.id == u_data["id"]))
        if not existing.scalar_one_or_none():
            user = User(
                id=u_data["id"],
                name=u_data["name"],
                email=u_data["email"],
                role=u_data["role"],
                hashed_password=get_password_hash(u_data["password"])
            )
            session.add(user)
            users_count += 1

    # 2. Seed Products & Inventory
    products_count = 0
    for p_data in PRODUCTS_SEED_DATA:
        existing = await session.execute(select(Product).where(Product.id == p_data["id"]))
        if not existing.scalar_one_or_none():
            product = Product(
                id=p_data["id"],
                sku=p_data["sku"],
                title=p_data["title"],
                category=p_data["category"],
                price_cents=p_data["price_cents"],
                stock_level=p_data["stock_level"],
                description=p_data["description"],
                active=True
            )
            session.add(product)
            
            # Associated inventory record
            inv = Inventory(
                product_id=p_data["id"],
                available_stock=p_data["stock_level"],
                reserved_stock=0
            )
            session.add(inv)
            products_count += 1

    # 3. Seed Orders & Order Items
    orders_count = 0
    for o_data in ORDERS_SEED_DATA:
        existing = await session.execute(select(Order).where(Order.id == o_data["id"]))
        if not existing.scalar_one_or_none():
            order = Order(
                id=o_data["id"],
                user_id=o_data["user_id"],
                order_status=o_data["order_status"],
                shipping_address=o_data["shipping_address"],
                total_cents=o_data["total_cents"],
                idempotency_key=o_data["idempotency_key"]
            )
            session.add(order)
            for it in o_data["items"]:
                order_item = OrderItem(
                    order_id=o_data["id"],
                    product_id=it["product_id"],
                    quantity=it["quantity"],
                    unit_price_cents=it["unit_price_cents"]
                )
                session.add(order_item)
            orders_count += 1

    await session.commit()
    return {
        "users_added": users_count,
        "products_added": products_count,
        "orders_added": orders_count,
        "total_products": len(PRODUCTS_SEED_DATA),
        "total_users": len(USERS_SEED_DATA)
    }

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        counts = await seed_database(session, reset=True)
        print("Database initialized and seeded successfully:", counts)

if __name__ == "__main__":
    asyncio.run(init_db())
