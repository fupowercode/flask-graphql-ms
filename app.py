from flask import Flask
from flask import render_template_string
from strawberry.flask.views import GraphQLView
from strawberry.schema import Schema
import strawberry
from datetime import datetime
from typing import List

app = Flask(__name__)

# Modelo de base de datos usando SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    precio = Column(Float)
    cantidad = Column(Integer)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Definir los tipos de datos y las operaciones GraphQL con Strawberry

@strawberry.type
class CartType:
    id: int
    nombre: str
    precio: float
    cantidad: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime

@strawberry.type
class Query:
    carts: List[CartType]

    @strawberry.field
    def all_carts(self) -> List[CartType]:
        session = SessionLocal()
        carts = session.query(Cart).all()
        session.close()
        return [CartType(**{key: value for key, value in vars(cart).items() if key != '_sa_instance_state'}) for cart in carts]


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_cart(self, nombre: str, precio: float, cantidad: int) -> CartType:
        session = SessionLocal()
        new_cart = Cart(nombre=nombre, precio=precio, cantidad=cantidad)
        session.add(new_cart)
        session.commit()
        session.refresh(new_cart)
        session.close()
        # Filtramos _sa_instance_state antes de pasar a CartType
        return CartType(**{key: value for key, value in vars(new_cart).items() if key != '_sa_instance_state'})


    @strawberry.mutation
    def update_cart(self, id: int, nombre: str, precio: float, cantidad: int) -> CartType:
        session = SessionLocal()
        cart = session.query(Cart).filter(Cart.id == id).first()
        cart.nombre = nombre
        cart.precio = precio
        cart.cantidad = cantidad
        cart.fecha_actualizacion = datetime.utcnow()
        session.commit()
        session.refresh(cart)
        session.close()
        return CartType(**{key: value for key, value in vars(cart).items() if key != '_sa_instance_state'})


    @strawberry.mutation
    def delete_cart(self, id: int) -> str:
        session = SessionLocal()
        cart = session.query(Cart).filter(Cart.id == id).first()
        if cart:
            session.delete(cart)
            session.commit()
            session.close()
            return f"Carrito {id} eliminado."
        session.close()
        return "Carrito no encontrado."

schema = strawberry.Schema(query=Query, mutation=Mutation)

# Configurar la vista de GraphQL con Strawberry
app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view("graphql_view", schema=schema),
)

@app.route('/')
def index():
    manual_html = """
    <html>
    <head>
        <title>Manual de Uso - API GraphQL</title>
    </head>
    <body>
        <h1>Bienvenido a la API de Carrito de Compras</h1>
        <p>Esta es una API simple para gestionar un carrito de compras utilizando GraphQL.</p>
        
        <h2>Consultas</h2>
        <h3>Obtener todos los carritos</h3>
        <pre><code>
query {
  allCarts {
    id
    nombre
    precio
    cantidad
    fechaCreacion
    fechaActualizacion
  }
}
        </code></pre>

        <h2>Mutaciones</h2>
        <h3>Crear un nuevo carrito</h3>
        <pre><code>
mutation {
  createCart(nombre: "Producto 1", precio: 10.99, cantidad: 2) {
    id
    nombre
    precio
    cantidad
    fechaCreacion
    fechaActualizacion
  }
}
        </code></pre>

        <h3>Actualizar un carrito existente</h3>
        <pre><code>
mutation {
  updateCart(id: 1, nombre: "Producto 1 Modificado", precio: 12.99, cantidad: 3) {
    id
    nombre
    precio
    cantidad
    fechaCreacion
    fechaActualizacion
  }
}
        </code></pre>

        <h3>Eliminar un carrito</h3>
        <pre><code>
mutation {
  deleteCart(id: 1)
}
        </code></pre>

        <h2>Acceso a GraphQL</h2>
        <p>Puedes acceder a la interfaz de GraphQL en <a href="/graphql">/graphql</a> para realizar consultas y mutaciones.</p>
    </body>
    </html>
    """
    return render_template_string(manual_html)

if __name__ == "__main__":
    app.run(debug=True)

