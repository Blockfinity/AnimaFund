/**
 * Anima Fund Wallet Management
 *
 * Creates and manages an EVM wallet for the agent's identity and payments.
 * The private key is the agent's sovereign identity.
 */
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";
import fs from "fs";
import path from "path";
const ANIMA_DIR = path.join(process.env.HOME || "/root", ".anima");
const WALLET_FILE = path.join(ANIMA_DIR, "wallet.json");
export function getAutomatonDir() {
    return ANIMA_DIR;
}
export function getWalletPath() {
    return WALLET_FILE;
}
/**
 * Get or create the automaton's wallet.
 * The private key IS the automaton's identity -- protect it.
 */
export async function getWallet() {
    if (!fs.existsSync(ANIMA_DIR)) {
        fs.mkdirSync(ANIMA_DIR, { recursive: true, mode: 0o700 });
    }
    if (fs.existsSync(WALLET_FILE)) {
        const walletData = JSON.parse(fs.readFileSync(WALLET_FILE, "utf-8"));
        const account = privateKeyToAccount(walletData.privateKey);
        return { account, isNew: false };
    }
    else {
        const privateKey = generatePrivateKey();
        const account = privateKeyToAccount(privateKey);
        const walletData = {
            privateKey,
            createdAt: new Date().toISOString(),
        };
        fs.writeFileSync(WALLET_FILE, JSON.stringify(walletData, null, 2), {
            mode: 0o600,
        });
        return { account, isNew: true };
    }
}
/**
 * Get the wallet address without loading the full account.
 */
export function getWalletAddress() {
    if (!fs.existsSync(WALLET_FILE)) {
        return null;
    }
    const walletData = JSON.parse(fs.readFileSync(WALLET_FILE, "utf-8"));
    const account = privateKeyToAccount(walletData.privateKey);
    return account.address;
}
/**
 * Load the full wallet account (needed for signing).
 */
export function loadWalletAccount() {
    if (!fs.existsSync(WALLET_FILE)) {
        return null;
    }
    const walletData = JSON.parse(fs.readFileSync(WALLET_FILE, "utf-8"));
    return privateKeyToAccount(walletData.privateKey);
}
export function walletExists() {
    return fs.existsSync(WALLET_FILE);
}
//# sourceMappingURL=wallet.js.map