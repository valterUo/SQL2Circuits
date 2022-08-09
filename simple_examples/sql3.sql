SELECT
    invoiceId,
    billingAddress
FROM
    invoices
WHERE billingAddress = '2nd Street' AND invoiceId = 1