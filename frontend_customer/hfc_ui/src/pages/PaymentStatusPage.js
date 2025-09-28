import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useSearchParams } from 'react-router-dom';
import { Loader, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { useCart } from '../contexts/CartContext';
import { checkPaymentStatus } from '../config/api'; // Import our new function

const PaymentStatusPage = () => {
    const [status, setStatus] = useState('loading'); // loading, success, failed, pending
    const [message, setMessage] = useState('Please wait while we confirm your payment.');
    const [searchParams] = useSearchParams();
    const { clearCart } = useCart();

    useEffect(() => {
        // PhonePe will redirect back to this page. We need to get the transaction ID from the URL.
        // NOTE: For PhonePe's POST redirect, you might need to handle form data on a serverless function.
        // For this implementation, we assume the ID is available or can be retrieved.
        // Let's simulate getting it from a hypothetical session or local storage for now.
        const transactionId = "a_simulated_transaction_id_from_before_redirect"; // This needs to be stored before redirecting

        const verifyPayment = async () => {
            if (transactionId) {
                try {
                    const result = await checkPaymentStatus(transactionId);
                    if (result && result.success) {
                        const paymentState = result.code;
                        if (paymentState === 'PAYMENT_SUCCESS') {
                            setStatus('success');
                            setMessage("Thank you for your order! We're preparing it now!");
                            clearCart(); // Clear the cart on successful payment
                        } else if (paymentState === 'PAYMENT_PENDING') {
                            setStatus('pending');
                            setMessage("Your payment is pending. We will update the status in 'My Orders' shortly.");
                            clearCart(); // Clear the cart as the order is placed
                        } else {
                            setStatus('failed');
                            setMessage("Your payment failed. Please try again or contact support.");
                        }
                    } else {
                        setStatus('failed');
                        setMessage(result.message || "Could not verify payment status.");
                    }
                } catch (error) {
                    setStatus('failed');
                    setMessage("An error occurred while verifying your payment.");
                }
            } else {
                setStatus('failed');
                setMessage("No transaction ID found. Your payment could not be verified.");
            }
        };
        
        // Simulate a 3-second delay to feel like a real verification process
        const timer = setTimeout(verifyPayment, 3000);
        return () => clearTimeout(timer);

    }, [searchParams, clearCart]);

    const renderStatus = () => {
        switch (status) {
            case 'success':
                return (
                    <>
                        <CheckCircle size={64} className="mx-auto text-green-500 mb-4" />
                        <h1 className="page-title">Payment Successful!</h1>
                        <p className="page-subtitle">{message}</p>
                        <Link to="/orders" className="auth-button" style={{marginTop: '1.5rem'}}>View My Orders</Link>
                    </>
                );
            case 'failed':
                return (
                    <>
                        <XCircle size={64} className="mx-auto text-red-500 mb-4" />
                        <h1 className="page-title">Payment Failed</h1>
                        <p className="page-subtitle">{message}</p>
                        <Link to="/orders" className="auth-button" style={{marginTop: '1.5rem'}}>Return to Cart</Link>
                    </>
                );
            case 'pending':
                 return (
                    <>
                        <AlertTriangle size={64} className="mx-auto text-yellow-500 mb-4" />
                        <h1 className="page-title">Payment Pending</h1>
                        <p className="page-subtitle">{message}</p>
                        <Link to="/orders" className="auth-button" style={{marginTop: '1.5rem'}}>Check My Orders</Link>
                    </>
                );
            default: // loading
                return (
                    <>
                        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                            <Loader size={64} className="mx-auto text-primary-vibrant" />
                        </motion.div>
                        <h1 className="page-title mt-4">Verifying Your Payment...</h1>
                        <p className="page-subtitle">{message}</p>
                    </>
                );
        }
    };

    return (
        <div className="page-container">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, type: "spring" }}
                className="login-card text-center"
            >
                {renderStatus()}
            </motion.div>
        </div>
    );
};

export default PaymentStatusPage;

