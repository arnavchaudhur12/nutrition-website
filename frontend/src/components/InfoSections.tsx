import { useState } from "react";

const termsSections = [
  {
    title: "1. General",
    body: [
      "By using this Website, you confirm that:",
      "You are at least 18 years of age or using the Website under the supervision of a parent or legal guardian.",
      "The information provided by you is accurate, complete, and current.",
      "You will use the Website only for lawful purposes.",
      "We reserve the right to update, modify, or change these Terms at any time without prior notice. Continued use of the Website after changes means you accept the updated Terms."
    ]
  },
  {
    title: "2. Business Information",
    body: [
      "Brand Name: Lagad's Nutrition",
      "Owner: Jai Lagad",
      "Website: www.lagadsnutrition.in",
      "Address: Jay Ganga Nagar, Keshav Nagar, Mundhwa, Pune - 411036, Maharashtra, India",
      "Email: Customercare@lagadsnutrition.in",
      "Instagram: @lagadsnutrition"
    ]
  },
  {
    title: "3. Products & Services",
    body: [
      "We sell products including but not limited to:",
      "Peanut Butter",
      "High Protein Oats",
      "Healthy Food Products",
      "Fitness Products",
      "All products displayed on the Website are subject to availability. We reserve the right to discontinue or modify any product without notice."
    ]
  },
  {
    title: "4. Orders",
    body: [
      "All orders placed through the Website are subject to acceptance and availability.",
      "Once an order is placed, you will receive an order confirmation.",
      "We reserve the right to refuse or cancel any order if fraudulent or unauthorized activity is suspected.",
      "Products purchased from the Website are intended for personal use only and not for resale."
    ]
  },
  {
    title: "5. Pricing & Payment",
    body: [
      "All prices listed on the Website are in Indian Rupees (INR) and inclusive of applicable taxes unless stated otherwise.",
      "We accept payments through UPI, debit cards, credit cards, net banking, and wallets.",
      "We reserve the right to modify product prices at any time without prior notice."
    ]
  },
  {
    title: "6. Shipping & Delivery",
    body: [
      "Order Processing Time: 1-2 working days",
      "Estimated Delivery Time: 4-7 working days",
      "Delivery timelines may vary depending on courier services, weather conditions, public holidays, or unforeseen circumstances.",
      "Customers are responsible for providing accurate shipping information. We are not responsible for delays or losses caused by incorrect addresses."
    ]
  },
  {
    title: "7. Cancellation Policy",
    body: [
      "Orders can only be cancelled before dispatch.",
      "Once the order has been shipped, cancellation requests will not be accepted.",
      "For cancellation requests, customers may contact us through our support email."
    ]
  },
  {
    title: "8. Refund & Replacement Policy",
    body: [
      "We only provide replacement/refund for damaged products received or wrong products delivered.",
      "An unboxing video is mandatory as proof.",
      "Claims must be raised within 24 hours of delivery.",
      "Opened or used food products cannot be returned or refunded.",
      "Refunds, if approved, will be processed within a reasonable timeframe."
    ]
  },
  {
    title: "9. Health Disclaimer",
    body: [
      "Products sold on this Website are not intended to diagnose, treat, cure, or prevent any disease.",
      "Results from fitness or nutrition products may vary from person to person depending on body type, diet, lifestyle, and consistency.",
      "Customers are advised to consult a healthcare professional before starting any nutritional or fitness-related product."
    ]
  },
  {
    title: "10. Intellectual Property",
    body: [
      "All content on this Website including logos, product images, videos, text, designs, and branding is the property of Lagad's Nutrition and protected under applicable intellectual property laws.",
      "Copying, reproducing, distributing, or using any Website content without written permission is strictly prohibited."
    ]
  },
  {
    title: "11. User Conduct",
    body: [
      "Users agree not to use the Website for unlawful activities, attempt unauthorized access to Website systems, upload malicious software or harmful content, or misuse the Website in any manner.",
      "Violation may result in termination of access and legal action."
    ]
  },
  {
    title: "12. Third-Party Links",
    body: [
      "The Website may contain links to third-party websites or social media platforms. We are not responsible for the content, policies, or practices of external websites."
    ]
  },
  {
    title: "13. Limitation Of Liability",
    body: [
      "Lagad's Nutrition shall not be liable for any indirect, incidental, or consequential damages arising from the use of this Website or products purchased through it.",
      "We do not guarantee uninterrupted or error-free operation of the Website."
    ]
  },
  {
    title: "14. Privacy",
    body: [
      "Customer information collected through the Website will be handled according to our Privacy Policy.",
      "By using the Website, you consent to the collection and use of information for order processing, customer support, and related business purposes."
    ]
  },
  {
    title: "15. Governing Law & Jurisdiction",
    body: [
      "These Terms shall be governed by the laws of India.",
      "Any disputes arising from the use of this Website shall fall under the jurisdiction of the courts located in Pune, Maharashtra."
    ]
  },
  {
    title: "16. Contact Information",
    body: [
      "Lagad's Nutrition",
      "Email: Customercare@lagadsnutrition.in",
      "Address: Jay Ganga Nagar, Keshav Nagar, Mundhwa, Pune - 411036, Maharashtra, India"
    ]
  }
];

export function InfoSections() {
  const [openTermTitle, setOpenTermTitle] = useState<string | null>(null);
  const selectedTerm = termsSections.find((section) => section.title === openTermTitle) ?? null;

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

      <section className="terms-section" id="terms-conditions">
        <div className="terms-intro">
          <p className="eyebrow">Terms & Conditions</p>
          <h2>Legal policies designed for clarity and trust</h2>
          <p>
            Browse policy headings below. Click any heading to view full details in a focused
            popup without cluttering the page.
          </p>
        </div>
        <div className="terms-grid">
          {termsSections.map((section) => (
            <article className="terms-card" key={section.title}>
              <button
                type="button"
                className="terms-open-button"
                onClick={() => setOpenTermTitle(section.title)}
              >
                <span>{section.title}</span>
              </button>
            </article>
          ))}
        </div>
      </section>

      {selectedTerm ? (
        <div className="terms-modal-overlay" role="dialog" aria-modal="true">
          <div className="terms-modal-card">
            <div className="terms-modal-header">
              <h3>{selectedTerm.title}</h3>
              <button
                type="button"
                className="icon-button"
                onClick={() => setOpenTermTitle(null)}
                aria-label="Close terms details"
              >
                x
              </button>
            </div>
            <div className="terms-modal-content">
              {selectedTerm.body.map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
