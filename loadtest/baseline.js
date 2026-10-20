import http from 'k6/http';
import { check, sleep, fail } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const LOGIN_PATH = __ENV.LOGIN_PATH || '/api/auth/login';
const ACCOUNTS_PATH = __ENV.ACCOUNTS_PATH || '/api/accounts';
const CATEGORIES_PATH = __ENV.CATEGORIES_PATH || '/api/categories';
const TRANSACTIONS_PATH = __ENV.TRANSACTIONS_PATH || '/api/transactions';
const TRANSACTIONS_QUERY = __ENV.TRANSACTIONS_QUERY || 'page=1&page_size=20';
const THINK_TIME = Number(__ENV.THINK_TIME || 1);

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800'],
    'http_req_duration{name:accounts}': [],
    'http_req_duration{name:categories}': [],
    'http_req_duration{name:transactions}': [],
  },
};

export function setup() {
  const email = __ENV.TEST_EMAIL;
  const password = __ENV.TEST_PASSWORD;
  if (!email || !password) {
    fail('TEST_EMAIL and TEST_PASSWORD must be set in the environment');
  }

  const res = http.post(
    `${BASE_URL}${LOGIN_PATH}`,
    JSON.stringify({ email, password }),
    { headers: { 'Content-Type': 'application/json' }, tags: { name: 'login' } },
  );

  const token = res.status === 200 ? res.json('access_token') : null;
  if (!token) {
    fail(`Login failed: status=${res.status}`);
  }
  return { token };
}

export default function (data) {
  const params = (name) => ({
    headers: { Authorization: `Bearer ${data.token}` },
    tags: { name },
  });

  const responses = http.batch([
    ['GET', `${BASE_URL}${ACCOUNTS_PATH}`, null, params('accounts')],
    ['GET', `${BASE_URL}${CATEGORIES_PATH}`, null, params('categories')],
    ['GET', `${BASE_URL}${TRANSACTIONS_PATH}?${TRANSACTIONS_QUERY}`, null, params('transactions')],
  ]);

  check(responses[0], { 'accounts 200': (r) => r.status === 200 });
  check(responses[1], { 'categories 200': (r) => r.status === 200 });
  check(responses[2], { 'transactions 200': (r) => r.status === 200 });

  sleep(THINK_TIME);
}