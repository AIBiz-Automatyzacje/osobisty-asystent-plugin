#!/usr/bin/env node
'use strict';

/**
 * zdalna-sesja — zarządzanie zdalnymi sesjami Claude Code (tmux + Remote Control) na VPS.
 *
 * Z lokalnego komputera odpalasz nazwane sesje na serwerze, bez ręcznego wchodzenia na VPS.
 * Sesja żyje w tmux i startuje z `claude --remote-control <nazwa> --dangerously-skip-permissions`.
 *
 * Połączenie i przełączanie usera są DEKLARATYWNE (żadnego zgadywania kluczy/userów):
 *   VPS_SSH      — cel dla `ssh` (alias z ~/.ssh/config, np. `vps`, ALBO user@host)
 *   VPS_RUN_AS   — user, pod którym odpalić Claude (stara nazwa VPS_REMOTE_USER też działa);
 *                  pusty przy logowaniu jako root = claude, w pozostałych przypadkach = user z logowania
 *
 * Dwa realne tryby:
 *   • Alias z kluczem (Ty): VPS_SSH=vps     → login jako claude, bez su
 *   • Świeży VPS po B1:     VPS_HOST=<ip>   → login root, su - claude (VPS_RUN_AS domyślnie claude)
 *
 * Użycie:
 *   node vps-session.js new <nazwa>     # nowa nazwana sesja z Remote Control
 *   node vps-session.js list            # żywe sesje na VPS
 *   node vps-session.js kill <nazwa>    # ubij sesję
 *   node vps-session.js attach <nazwa>  # wypisz komendę do podglądu w terminalu
 *   (dowolna akcja + --dry-run pokazuje budowaną komendę, bez łączenia z serwerem)
 */

const { execFileSync } = require('node:child_process');
const { loadEnv } = require('./env_loader');

// Nazwa sesji trafia do komend shellowych na VPS — twarda walidacja = ochrona przed injection.
const SESSION_NAME_RE = /^[a-zA-Z0-9_-]{1,40}$/;

function validateName(name) {
  if (!name) {
    throw new Error('Podaj nazwę sesji, np. `new marketing`.');
  }
  if (!SESSION_NAME_RE.test(name)) {
    throw new Error(`Niedozwolona nazwa "${name}". Dozwolone: litery, cyfry, - i _ (max 40 znaków).`);
  }
  return name;
}

// Skrypt bash wykonywany na VPS. Nazwa jest już zwalidowana (alfanumeryczna).
function buildInner(action, name, cfg) {
  switch (action) {
    case 'new':
      // PATH-prefix ~/.local/bin: preferuj natywną instalację Claude (nowszą) nad ewentualnym
      // starym npm-globalem w /usr/bin. Ustawiane w pane, tuż przed exec — niezależne od env tmux servera.
      return `tmux new -d -s ${name} 'export PATH="$HOME/.local/bin:$PATH"; cd ${cfg.vaultPath} && exec claude --remote-control ${name} --dangerously-skip-permissions'`;
    case 'list':
      return 'tmux list-sessions 2>/dev/null || echo "(brak aktywnych sesji)"';
    case 'kill':
      return `tmux kill-session -t ${name}`;
    default:
      throw new Error(`Nieznana akcja: ${action}`);
  }
}

// Opcjonalne przełączenie usera: pusty runAs = odpal jako user z logowania (bez su).
function wrapRunAs(command, cfg) {
  return cfg.runAs ? `su - ${cfg.runAs} -c '${command}'` : command;
}

// Owija wewnętrzny skrypt w base64, żeby uniknąć piekła zagnieżdżonego cytowania ssh → su -c → tmux.
function buildRemoteCommand(action, name, cfg) {
  const inner = buildInner(action, name, cfg);
  const encoded = Buffer.from(inner, 'utf8').toString('base64');
  return `echo '${encoded}' | base64 -d | ${wrapRunAs('bash -s', cfg)}`;
}

// Attach jest interaktywny (wymaga TTY) — skill go nie odpala, tylko wypisuje gotowca do wklejenia.
function buildAttachCommand(name, cfg) {
  return `ssh -t ${cfg.sshTarget} "${wrapRunAs(`tmux attach -t ${name}`, cfg)}"`;
}

// Root ma zablokowane --dangerously-skip-permissions, więc przy logowaniu jako root
// bez jawnego VPS_RUN_AS przełączamy się na claude. VPS_REMOTE_USER = stara nazwa z dokumentacji.
function resolveConfig(env) {
  const sshExplicit = env.VPS_SSH;
  const host = env.VPS_HOST;
  const sshUser = env.VPS_USER || 'root';
  const sshTarget = sshExplicit || `${sshUser}@${host || ''}`;
  const explicitRunAs = (env.VPS_RUN_AS || env.VPS_REMOTE_USER || '').trim();
  const loginAsRoot = sshExplicit ? /^root@/.test(sshExplicit) : sshUser === 'root';
  return {
    sshTarget,
    runAs: explicitRunAs || (loginAsRoot ? 'claude' : ''),
    vaultPath: env.VPS_VAULT_PATH || '/home/claude/vault',
    hasConnection: Boolean(sshExplicit || host),
  };
}

function loadConfig() {
  loadEnv(__dirname);
  return resolveConfig(process.env);
}

function requireConnection(cfg) {
  if (!cfg.hasConnection) {
    throw new Error(
      'Brak danych serwera w .env. Dodaj JEDNO z:\n' +
      '  VPS_SSH=vps                         (alias z ~/.ssh/config — zalecane)\n' +
      '  VPS_HOST=<ip>                       (świeży VPS, login jako root, Claude pod userem claude)'
    );
  }
}

function runRemote(action, name, cfg, dryRun) {
  const remoteCommand = buildRemoteCommand(action, name, cfg);
  if (dryRun) {
    console.log(`# ssh ${cfg.sshTarget}:\n${remoteCommand}\n\n# skrypt wykonywany na VPS:\n${buildInner(action, name, cfg)}`);
    return;
  }
  execFileSync('ssh', [cfg.sshTarget, remoteCommand], { stdio: 'inherit' });
}

const USAGE = `zdalna-sesja — zdalne sesje Claude Code na VPS

  new <nazwa>     nowa nazwana sesja z Remote Control
  list            żywe sesje na VPS
  kill <nazwa>    ubij sesję
  attach <nazwa>  komenda do podglądu sesji w terminalu

  dodaj --dry-run do dowolnej akcji, żeby zobaczyć komendę bez łączenia z serwerem`;

function main(argv) {
  const args = argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const positional = args.filter((a) => !a.startsWith('--'));
  const action = positional[0];
  const name = positional[1];

  if (!action || action === 'help') {
    console.log(USAGE);
    return;
  }

  const cfg = loadConfig();

  switch (action) {
    case 'new':
    case 'kill': {
      validateName(name);
      if (!dryRun) requireConnection(cfg);
      runRemote(action, name, cfg, dryRun);
      if (action === 'new' && !dryRun) {
        console.log(`✅ Sesja "${name}" wystartowała na VPS. Podłącz się z telefonu/weba przez Remote Control (nazwa: ${name}).`);
      }
      break;
    }
    case 'list': {
      if (!dryRun) requireConnection(cfg);
      runRemote('list', null, cfg, dryRun);
      break;
    }
    case 'attach': {
      validateName(name);
      requireConnection(cfg);
      console.log('Wklej w SWOIM terminalu (attach jest interaktywny):\n');
      console.log(`  ${buildAttachCommand(name, cfg)}\n`);
      console.log('Wyjście z podglądu bez ubijania sesji: Ctrl+B, potem D.');
      break;
    }
    default:
      console.error(`Nieznana akcja: ${action}\n`);
      console.log(USAGE);
      process.exitCode = 1;
  }
}

if (require.main === module) {
  try {
    main(process.argv);
  } catch (err) {
    console.error(`❌ ${err.message}`);
    process.exitCode = 1;
  }
}

module.exports = { validateName, resolveConfig, buildInner, buildRemoteCommand, buildAttachCommand, wrapRunAs, main };
