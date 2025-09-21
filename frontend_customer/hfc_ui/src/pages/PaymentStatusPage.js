import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle } from 'lucide-react';
import { useCart } from '../contexts/CartContext'; // Assuming you have a clearCart function

const PaymentStatusPage = () => {
    // In a real app, you would get the status from the URL or a server call
    const isSuccess = true; // For demonstration purposes

    // const { clearCart } = useCart();
    // useEffect(() => {
    //     if (isSuccess) {
    //         clearCart(); // Clear the cart on successful payment
    //     }
    // }, [isSuccess, clearCart]);

    return (
        <div className="page-container">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, type: "spring" }}
                className="login-card text-center"
            >
                {isSuccess ? (
                    <>
                        <CheckCircle size={64} className="mx-auto text-green-500 mb-4" />
                        <h1 className="page-title">Payment Successful!</h1>
                        <p className="page-subtitle">Thank you for your order. We're preparing it now!</p>
                    </>
                ) : (
                    <>
                        <XCircle size={64} className="mx-auto text-red-500 mb-4" />
                        <h1 className="page-title">Payment Failed</h1>
                        <p className="page-subtitle">Something went wrong with your payment. Please try again.</p>
                    </>
                )}
            </motion.div>
        </div>
    );
};

export default PaymentStatusPage;
