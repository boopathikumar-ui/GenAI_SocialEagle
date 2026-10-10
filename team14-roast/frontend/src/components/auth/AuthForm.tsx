import { Alert, AlertIcon, FormControl, FormErrorMessage, FormLabel, Input, VStack } from '@chakra-ui/react';
import { useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { GradientButton } from '../ui/GradientButton';
import { getErrorMessage } from '../../services/authService';

export interface AuthFormValues {
  email: string;
  password: string;
  fullName: string;
}

type AuthMode = 'login' | 'register';
type FieldErrors = Partial<Record<keyof AuthFormValues, string>>;

interface AuthFormProps {
  mode: AuthMode;
  onSubmit: (values: AuthFormValues) => Promise<void>;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(values: AuthFormValues, mode: AuthMode): FieldErrors {
  const errors: FieldErrors = {};
  if (!EMAIL_RE.test(values.email.trim())) errors.email = 'Enter a valid email address';
  if (mode === 'register') {
    if (values.fullName.trim().length < 2) errors.fullName = 'Enter your name';
    if (values.password.length < 8) errors.password = 'Password must be at least 8 characters';
  } else if (values.password.length === 0) {
    errors.password = 'Password is required';
  }
  return errors;
}

export function AuthForm({ mode, onSubmit }: AuthFormProps) {
  const [values, setValues] = useState<AuthFormValues>({ email: '', password: '', fullName: '' });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const setField =
    (key: keyof AuthFormValues) =>
    (e: ChangeEvent<HTMLInputElement>): void => {
      const { value } = e.target;
      setValues((v) => ({ ...v, [key]: value }));
    };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    const found = validate(values, mode);
    setErrors(found);
    setFormError(null);
    if (Object.keys(found).length > 0) return;
    setSubmitting(true);
    try {
      await onSubmit({ ...values, email: values.email.trim(), fullName: values.fullName.trim() });
    } catch (err: unknown) {
      setFormError(getErrorMessage(err, mode === 'login' ? 'Login failed' : 'Registration failed'));
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} noValidate>
      <VStack spacing={4}>
        {formError && (
          <Alert status="error" rounded="md">
            <AlertIcon />
            {formError}
          </Alert>
        )}
        {mode === 'register' && (
          <FormControl isInvalid={Boolean(errors.fullName)}>
            <FormLabel>Full name</FormLabel>
            <Input value={values.fullName} onChange={setField('fullName')} autoComplete="name" />
            <FormErrorMessage>{errors.fullName}</FormErrorMessage>
          </FormControl>
        )}
        <FormControl isInvalid={Boolean(errors.email)}>
          <FormLabel>Email</FormLabel>
          <Input type="email" value={values.email} onChange={setField('email')} autoComplete="email" />
          <FormErrorMessage>{errors.email}</FormErrorMessage>
        </FormControl>
        <FormControl isInvalid={Boolean(errors.password)}>
          <FormLabel>Password</FormLabel>
          <Input
            type="password"
            value={values.password}
            onChange={setField('password')}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
          <FormErrorMessage>{errors.password}</FormErrorMessage>
        </FormControl>
        <GradientButton type="submit" w="full" isLoading={submitting}>
          {mode === 'login' ? 'Log in' : 'Create account'}
        </GradientButton>
      </VStack>
    </form>
  );
}
