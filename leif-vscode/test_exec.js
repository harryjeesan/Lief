const { exec } = require('child_process');
exec('python -c "print(undefined_variable)" 2>&1', (error, stdout, stderr) => {
    console.log('ERROR_OBJECT:', error ? error.message : null);
    console.log('STDOUT:', stdout);
    console.log('STDERR:', stderr);
});
