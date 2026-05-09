export function InfoSections() {
  return (
    <>
      <section className="split-section" id="about-us">
        <div>
          <p className="eyebrow">About Us</p>
          <h2>Lagads Nutrition is built around flavour-first everyday nutrition</h2>
        </div>
        <p>
          The brand identity leans confident, warm, and energetic. The website architecture is
          designed so the business can evolve from a focused peanut butter catalog into a broader
          nutrition storefront without a redesign of the core platform.
        </p>
      </section>

      <section className="split-section" id="customer-feedback">
        <div>
          <p className="eyebrow">Customer Feedback</p>
          <h2>Collect reviews, ratings, and repeat purchase signals</h2>
        </div>
        <p>
          Feedback data is planned as a first-class backend entity so your dashboard can track
          product satisfaction, review volume, and sentiment trends without mixing analytics logic
          into product management code.
        </p>
      </section>

      <section className="newsletter-box" id="newsletter">
        <div>
          <p className="eyebrow">Newsletter</p>
          <h2>Turn new visitors into repeat customers</h2>
          <p>Capture email interest for launches, new flavours, offers, and reorder reminders.</p>
        </div>
        <form className="newsletter-form">
          <input type="email" placeholder="Enter your email address" />
          <button type="button" className="pill pill-primary">
            Subscribe
          </button>
        </form>
      </section>
    </>
  );
}

