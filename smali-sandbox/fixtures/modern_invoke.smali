.class public Lcom/example/MethodHandleUser;
.super Ljava/lang/Object;

.method public polyVirtual(Ljava/lang/invoke/MethodHandle;Ljava/lang/Object;)Ljava/lang/Object;
    .registers 4
    invoke-polymorphic {p1, p2}, Ljava/lang/invoke/MethodHandle;->invoke([Ljava/lang/Object;)Ljava/lang/Object;, (Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v0
    return-object v0
.end method

.method public polyRange(Ljava/lang/invoke/MethodHandle;Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    .registers 5
    invoke-polymorphic/range {p1 .. p3}, Ljava/lang/invoke/MethodHandle;->invoke([Ljava/lang/Object;)Ljava/lang/Object;, (Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;
    move-result-object v0
    return-object v0
.end method

.method public customInvoke(Ljava/lang/Object;)V
    .registers 2
    invoke-custom {p1}, lambda-0, (Ljava/lang/Object;)V
    return-void
.end method
