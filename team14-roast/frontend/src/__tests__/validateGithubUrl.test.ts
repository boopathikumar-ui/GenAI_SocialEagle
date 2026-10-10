import { describe, expect, it } from 'vitest';
import { validateGithubUrl } from '../services/roastService';

describe('validateGithubUrl', () => {
  it.each([
    'https://github.com/octocat',
    'https://www.github.com/octocat/',
    'https://github.com/octocat/Hello-World',
    '  https://github.com/octocat/repo.name_1  ',
  ])('accepts %s', (url) => {
    expect(validateGithubUrl(url)).toBeNull();
  });

  it('asks for input when empty', () => {
    expect(validateGithubUrl('')).toMatch(/enter/i);
    expect(validateGithubUrl('   ')).toMatch(/enter/i);
  });

  it.each([
    'http://github.com/octocat',
    'github.com/octocat',
    'https://github.com.evil.com/octocat',
    'https://evilgithub.com/octocat',
    'https://github.com@evil.com/octocat',
    'https://github.com/',
    'https://github.com/a/b/c',
    'https://github.com/-bad',
    'https://github.com/octocat?x=1',
    'javascript:alert(1)',
    'https://localhost/octocat',
    'https://github.com/' + 'a'.repeat(40),
  ])('rejects %s', (url) => {
    expect(validateGithubUrl(url)).toMatch(/use a url/i);
  });
});
