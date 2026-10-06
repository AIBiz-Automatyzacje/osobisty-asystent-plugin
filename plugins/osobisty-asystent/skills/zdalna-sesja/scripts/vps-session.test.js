'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { validateName, resolveConfig, buildInner, buildRemoteCommand, buildAttachCommand } = require('./vps-session');

// Tryb "świeży VPS": login root, przełączenie na claude przez su.
const CFG_SU = {
  sshTarget: 'root@100.86.100.113',
  runAs: 'claude',
  vaultPath: '/home/claude/vault',
};

// Tryb "alias z kluczem": login od razu jako claude, bez su.
const CFG_DIRECT = {
  sshTarget: 'vps',
  runAs: '',
  vaultPath: '/home/claude/vault',
};

test('validateName — akceptuje poprawne nazwy', () => {
  assert.equal(validateName('marketing'), 'marketing');
  assert.equal(validateName('klient-x_2'), 'klient-x_2');
});

test('validateName — odrzuca puste i niebezpieczne nazwy', () => {
  assert.throws(() => validateName(''), /Podaj nazwę/);
  assert.throws(() => validateName(undefined), /Podaj nazwę/);
  assert.throws(() => validateName('a; rm -rf /'), /Niedozwolona/);
  assert.throws(() => validateName('$(whoami)'), /Niedozwolona/);
  assert.throws(() => validateName('a'.repeat(41)), /Niedozwolona/);
});

test('buildInner new — zawiera obie flagi, nazwę sesji i PATH-prefix', () => {
  const inner = buildInner('new', 'research', CFG_SU);
  assert.match(inner, /tmux new -d -s research/);
  assert.match(inner, /export PATH="\$HOME\/\.local\/bin:\$PATH"/);
  assert.match(inner, /cd \/home\/claude\/vault/);
  assert.match(inner, /claude --remote-control research --dangerously-skip-permissions/);
});

test('buildInner list — nie wywala się przy braku sesji', () => {
  const inner = buildInner('list', null, CFG_SU);
  assert.match(inner, /tmux list-sessions/);
  assert.match(inner, /brak aktywnych sesji/);
});

test('buildInner kill — celuje w nazwaną sesję', () => {
  assert.match(buildInner('kill', 'research', CFG_SU), /tmux kill-session -t research/);
});

test('buildInner — nieznana akcja rzuca', () => {
  assert.throws(() => buildInner('nope', 'x', CFG_SU), /Nieznana akcja/);
});

test('buildRemoteCommand — base64 dekoduje się z powrotem do inner (round-trip)', () => {
  const inner = buildInner('new', 'marketing', CFG_SU);
  const remote = buildRemoteCommand('new', 'marketing', CFG_SU);
  const encoded = remote.match(/echo '([A-Za-z0-9+/=]+)'/)[1];
  const decoded = Buffer.from(encoded, 'base64').toString('utf8');
  assert.equal(decoded, inner);
});

test('buildRemoteCommand — runAs owija w su, pusty runAs pomija su', () => {
  assert.match(buildRemoteCommand('new', 'marketing', CFG_SU), /\| su - claude -c 'bash -s'/);
  const direct = buildRemoteCommand('new', 'marketing', CFG_DIRECT);
  assert.match(direct, /\| bash -s$/);
  assert.doesNotMatch(direct, /su -/);
});

test('buildAttachCommand — su vs bezpośrednio, zawsze ssh -t z nazwą sesji', () => {
  const withSu = buildAttachCommand('research', CFG_SU);
  assert.match(withSu, /ssh -t root@100\.86\.100\.113/);
  assert.match(withSu, /su - claude -c 'tmux attach -t research'/);

  const direct = buildAttachCommand('research', CFG_DIRECT);
  assert.match(direct, /ssh -t vps "tmux attach -t research"/);
  assert.doesNotMatch(direct, /su -/);
});

test('resolveConfig — login root przez VPS_HOST domyślnie przełącza na claude', () => {
  const cfg = resolveConfig({ VPS_HOST: '100.1.2.3' });
  assert.equal(cfg.sshTarget, 'root@100.1.2.3');
  assert.equal(cfg.runAs, 'claude');
});

test('resolveConfig — VPS_RUN_AS i stara nazwa VPS_REMOTE_USER', () => {
  assert.equal(resolveConfig({ VPS_HOST: 'h', VPS_RUN_AS: 'asystent' }).runAs, 'asystent');
  assert.equal(resolveConfig({ VPS_HOST: 'h', VPS_REMOTE_USER: 'asystent' }).runAs, 'asystent');
  assert.equal(resolveConfig({ VPS_HOST: 'h', VPS_RUN_AS: 'a', VPS_REMOTE_USER: 'b' }).runAs, 'a');
});

test('resolveConfig — alias albo login nie-root bez su', () => {
  assert.equal(resolveConfig({ VPS_SSH: 'vps' }).runAs, '');
  assert.equal(resolveConfig({ VPS_HOST: 'h', VPS_USER: 'claude' }).runAs, '');
  assert.equal(resolveConfig({ VPS_SSH: 'root@h' }).runAs, 'claude');
});
