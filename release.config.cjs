module.exports = {
  branches: [
    'main',
    { name: 'staging', prerelease: 'rc' },
  ],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    ['@semantic-release/npm', { npmPublish: false }],
    ['@semantic-release/github', {
      successComment: false,
      failComment: false,
      failTitle: false,
      labels: false,
      releasedLabels: false,
      addReleases: 'bottom'
    }],
    ['@semantic-release/git', {
      assets: ['package.json'],
      message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
    }]
  ],
  preset: 'angular',
  onError: (error, { errors }) => {
    // Filter out "NOT_FOUND" errors related to issues and pull requests
    if (error.name === 'AggregateError') {
      const filteredErrors = errors.filter(err => {
        if (err.type === 'NOT_FOUND') {
          const path = err.path.join('.');
          return !(path.includes('issue') || path.includes('pull') || path.includes('pr'));
        }
        return true;
      });
      
      // If all errors were filtered out, return null to indicate success
      if (filteredErrors.length === 0) {
        return null;
      }
      
      // Otherwise, return the filtered errors
      error.errors = filteredErrors;
    }
    return error;
  }
};
