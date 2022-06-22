SELECT
    invoiceId,
    billingAddress,
    total
FROM
    invoices
WHERE total BETWEEN 14.91 AND 18.86 
    AND billingAddress = 'Murattikatu'
    AND invoiceId = 3