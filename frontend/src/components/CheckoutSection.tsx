export function CheckoutSection() {
  return (
    <section className="checkout-shell" id="checkout">
      <div>
        <p className="eyebrow">Checkout workflow</p>
        <h2>Login before payment, then confirm delivery details</h2>
        <p>
          Users add products to cart first, then log in or register, fill delivery details,
          review comments and continue to the payment gateway. Both the buyer and admin receive
          a confirmation email after successful payment.
        </p>
      </div>

      <form className="checkout-form">
        <label className="field">
          <span>Full Name</span>
          <input placeholder="Enter full name" />
        </label>
        <label className="field">
          <span>Delivery Address</span>
          <textarea placeholder="House number, street, city, state, pin code" rows={4} />
        </label>
        <label className="field">
          <span>Phone Number</span>
          <input placeholder="Primary mobile number" />
        </label>
        <label className="field">
          <span>Email Address</span>
          <input placeholder="your@email.com" />
        </label>
        <label className="field">
          <span>Alternative Phone Number</span>
          <input placeholder="Optional alternate mobile number" />
        </label>
        <label className="field">
          <span>Comments or Special Request</span>
          <textarea placeholder="Any delivery notes or preferences" rows={3} />
        </label>
        <button type="button" className="pill pill-primary">
          Continue to Payment Gateway
        </button>
      </form>
    </section>
  );
}

