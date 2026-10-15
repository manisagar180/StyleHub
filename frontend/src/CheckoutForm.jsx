import { useState } from "react";
import {
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";

export default function CheckoutForm({ onSuccess, onCancel }) {
  const stripe = useStripe();
  const elements = useElements();
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    if (!stripe || !elements || processing) return;

    setProcessing(true);
    setErrorMessage("");

    try {
      const result = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/`,
        },
        redirect: "if_required",
      });

      if (result.error) {
        setErrorMessage(
          result.error.message || "Payment could not be completed."
        );
        return;
      }

      if (result.paymentIntent?.status === "succeeded") {
        onSuccess?.();
      } else {
        setErrorMessage(
          "Payment has not completed yet. Check your order status before retrying."
        );
      }
    } catch {
      setErrorMessage("Unable to confirm payment. Please try again.");
    } finally {
      setProcessing(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stripe-checkout-form">
      <PaymentElement />

      {errorMessage && (
        <p role="alert" className="stripe-error">
          {errorMessage}
        </p>
      )}

      <button
        type="submit"
        className="button-dark checkout-button"
        disabled={!stripe || !elements || processing}
      >
        {processing ? "Processing…" : "Pay securely"}
      </button>

      <button
        type="button"
        className="stripe-cancel-button"
        onClick={onCancel}
        disabled={processing}
      >
        Cancel
      </button>
    </form>
  );
}